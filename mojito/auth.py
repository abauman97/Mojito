"""Authentication and authorization utilities to reduce the boilerplate required to implement basic session
based authentication."""

import functools
import hashlib
import typing as t

from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .config import Config
from .globals import g


class AuthSessionData(t.TypedDict):
    "The authentication data stored on the session"

    is_authenticated: bool
    auth_handler: t.Optional[str]
    'The name of the auth handler class used to authenticate the user. Ex: "PasswordAuth"'
    user_id: t.Any
    user: dict[str, t.Any]
    """The user object. May contain any information about the user, such as name and user_id that
    you want to be available anywhere with access to the request. Don't store any sensitive
     information like passwords as all of this will be encoded and stored on the session but may
     be decoded by anyone who inspects the cookie."""
    permissions: list[str]
    "permissions are used to authorize the user. Think of them as scopes in a JWT."


class BaseAuth(t.Protocol):
    """Base class that all authentication methods should implement."""

    async def authenticate(
        self, request: Request, **kwargs: dict[str, t.Any]
    ) -> t.Optional[AuthSessionData]:
        """Method to authenticate the user based on the users username and password. Will
        be used by the password_login() function to authenticate the user.

        Args:
            request (Request): Mojito/Starlette request object
            **kwargs (P.kwargs): The credentials to use in authorization as keyword only arguments

        Raises:
            NotImplementedError: Method not implemented

        Returns:
            AuthSessionData | None: The auth data stored on the session.
        """
        raise NotImplementedError()

    async def get_user(self, user_id: t.Any) -> AuthSessionData:
        """Fetch the user based on user_id. Used when revalidating the user without requiring
        reauthentication.

        Implementation should get the latest permissions and verify the user is still active.

        Args:
            user_id (Any): Unique ID to locate the user in storage.
        """
        raise NotImplementedError()


class _AuthConfig:
    default_handler: t.Optional[str] = None
    "Name of the default hanlder class"
    auth_handlers: dict[str, type[BaseAuth]] = {}

    @staticmethod
    def get_default_handler():
        if not _AuthConfig.default_handler:
            raise NotImplementedError(
                "must set a default auth handler using set_auth_handler()"
            )
        return _AuthConfig.default_handler


def include_auth_handler(auth_handler: type[BaseAuth], primary: bool = False):
    """Include an auth handler for use. If this is the first or only auth handler included, it
    will be set as primary regardless of the value of the primary argument.

    Args:
        auth_handler (type[BaseAuth]): The class auth handler class.
        primary (bool, optional): Set the class as the primary/default auth handler. Defaults to False.
    """
    handler_name = auth_handler.__name__
    print(f"set handler name: {handler_name}")
    _AuthConfig.auth_handlers[handler_name] = auth_handler
    if primary or len(_AuthConfig.auth_handlers) == 1:
        _AuthConfig.default_handler = handler_name


async def _check_session_auth(request: Request, allowed_permissions: list[str]) -> bool:
    if not request.session:
        return False
    session_data = AuthSessionData(
        is_authenticated=request.session.get("is_authenticated", False),
        auth_handler=request.session.get("auth_handler", _AuthConfig.default_handler),
        user_id=request.session.get("user_id"),
        user=request.session.get("user", {}),
        permissions=request.session.get("permissions", []),
    )
    if not session_data["is_authenticated"]:
        # Revalidate on session exists but is not authenticated
        if not _AuthConfig.default_handler:
            raise NotImplementedError(
                "an auth handler must be set using set_auth_handler"
            )
        handler = _AuthConfig.auth_handlers[session_data["auth_handler"]]  # type:ignore
        data = await handler().get_user(session_data["user_id"])
        request.session.update(data)
    for allowed_permission in allowed_permissions:
        if not allowed_permission in session_data["permissions"]:
            return False
    return True


class AuthMiddleware:
    """Uses sessions to authorize and authenticate users with requests.
    Redirect to login_url if session is not authenticated or if user does not have the required auth scopes.
    Can be applied at the app level or on individual routers.

    Will ignore the Config.LOGIN_URL path to prevent infinite redirects.

    Args:
        ignore_routes (Optional[list[str]]): defaults to None. paths of routes to ignore validation on like '/login'. Path should be relative
            and match the Request.url.path value when the route is called.
        allow_permissions (Optional[list[str]]): defaults to None. List of scopes the user must have in order to be authorized
            to access the requested resource.
    """

    def __init__(
        self,
        app: ASGIApp,
        ignore_routes: list[str] = [],
        allow_permissions: list[str] = [],
    ) -> None:
        self.app = app
        self.ignore_routes = ignore_routes
        self.allow_permissions = allow_permissions

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request = Request(scope, receive)

        async def send_wrapper(message: Message) -> None:
            # ... Do something
            if (
                request.url.path in self.ignore_routes
                or request.url.path == Config.LOGIN_URL
            ):
                # Skip for routes registered as login_not_required
                return await send(message)
            allowed = await _check_session_auth(request, self.allow_permissions)
            if not allowed:
                response = RedirectResponse(Config.LOGIN_URL, 302)
                return await response(scope, receive, send)
            await send(message)

        await self.app(scope, receive, send_wrapper)


def require_auth(
    allow_permissions: list[str] = [], redirect_url: t.Optional[str] = None
):
    """Decorator to require that the user is authenticated and optionally check that the user has
    the required auth scopes before accessing the resource. Redirect to the configured
    login_url if one is set, or to redirect_url if one is given.

    Args:
        scopes (Optional[list[str]]): Auth scopes to verify the user has. Defaults to None.
        redirect_url (Optional[list[str]]): Redirect to this url rather than the configured
            login_url.
    """
    # This decorator must be applied below the route definition decorator so that it will wrap the
    # endpoint function before the route decorator will. This decorator will pass all arg straight
    # through after verifying authentication or else it will return a redirect response.

    def wrapper(func: t.Callable[..., t.Any]):
        @functools.wraps(func)
        async def requires_auth_function(*args: t.Any, **kwargs: dict[str, t.Any]):
            request = g.request
            assert isinstance(request, Request)
            REDIRECT_URL = redirect_url if redirect_url else Config.LOGIN_URL
            allow = await _check_session_auth(request, allow_permissions)
            if not allow:
                return RedirectResponse(REDIRECT_URL, 302)
            return func(*args, **kwargs)

        return requires_auth_function

    return wrapper


def hash_password(password: str) -> str:
    """Helper to hash a password before storing it or to compare a plain text password to the one stored.

    Args:
        password (str): The plain text password to hash.

    Returns:
        str: The hashed password.
    """
    return hashlib.sha256(password.encode()).hexdigest()


async def login(
    request: Request,
    auth_handler: t.Optional[type[BaseAuth]] = None,
    **kwargs: t.Any,
):
    """Login user and create an authenticated session.

    Args:
        request (Request): the request
        auth_handler (type[BaseAuth], optional): Auth class to login with.
            Defaults to the default auth handler configured using set_auth_handler().

    Returns:
        AuthSessionData: The data set on the session. None if invalid login.
    """
    if not auth_handler:
        auth_handler = _AuthConfig.auth_handlers[_AuthConfig.get_default_handler()]
    handler = auth_handler()
    result = await handler.authenticate(request, **kwargs)
    if not result:
        return None
    request.session.update(result)
    return result


def logout(request: Request):
    """Expire the current user session."""
    request.session.clear()
