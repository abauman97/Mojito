"""Authentication and authorization utilities to reduce the boilerplate required to implement basic session
based authentication."""

import functools
import hashlib
import sys
import typing as t

if sys.version_info >= (3, 10):  # pragma: no cover
    from typing import ParamSpec
else:  # pragma: no cover
    from typing_extensions import ParamSpec

from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .config import Config


class AuthSessionData(t.TypedDict):
    """The authentication data stored on the user session."""

    is_authenticated: bool
    auth_handler: t.Optional[str]
    'The name of the auth handler class used to authenticate the user. Ex: "PasswordAuth"'
    user_id: t.Any
    data: dict[str, t.Any]
    """The user data dict. May contain any additional data about the user, such as name and tenant_id that
    you want to be available anywhere with access to the request. Don't store any sensitive
    information like passwords as all of this will be encoded and stored on the user session but may
    be decoded by anyone who inspects the cookie."""
    permissions: list[str]
    "Permissions are used to authorize the user. Think of them as scopes in a JWT."


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
    def get_default_handler() -> str:
        if not _AuthConfig.default_handler:
            raise NotImplementedError(
                "must set a default auth handler using set_auth_handler()"
            )
        return _AuthConfig.default_handler


def include_auth_handler(auth_handler: type[BaseAuth], primary: bool = False) -> None:
    """Include an auth handler for use. If this is the first or only auth handler included, it
    will be set as primary regardless of the value of the primary argument.

    Args:
        auth_handler (type[BaseAuth]): The class auth handler class.
        primary (bool, optional): Set the class as the primary/default auth handler. Defaults to False.
    """
    handler_name = auth_handler.__name__
    _AuthConfig.auth_handlers[handler_name] = auth_handler
    if primary or len(_AuthConfig.auth_handlers) == 1:
        _AuthConfig.default_handler = handler_name


async def _check_session_auth(request: Request, allowed_permissions: list[str]) -> bool:
    if not request.user:
        return False
    auth_session_data = AuthSessionData(
        is_authenticated=request.user.get("is_authenticated", False),
        auth_handler=request.user.get("auth_handler", _AuthConfig.default_handler),
        user_id=request.user.get("user_id"),
        data=request.user.get("user", {}),
        permissions=request.user.get("permissions", []),
    )
    if not auth_session_data["is_authenticated"]:
        # Revalidate on session exists but is not authenticated
        if not _AuthConfig.default_handler:
            raise NotImplementedError(
                "an auth handler must be set using set_auth_handler"
            )
        handler = _AuthConfig.auth_handlers[auth_session_data["auth_handler"]]  # type:ignore
        data = await handler().get_user(auth_session_data["user_id"])
        request.user.update(data)
    if (
        Config.SUPERUSER_PERMISSION_NAME
        and Config.SUPERUSER_PERMISSION_NAME in auth_session_data["permissions"]
    ):
        return True
    for allowed_permission in allowed_permissions:
        if not allowed_permission in auth_session_data["permissions"]:
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


_P = ParamSpec("_P")


def requires(
    scopes: t.Union[str, t.Sequence[str]] = [],
    redirect_url: t.Optional[str] = None,
) -> t.Callable[[t.Callable[_P, t.Any]], t.Callable[_P, t.Any]]:
    """Decorator to require that the user is authenticated and optionally check that the user has
    the required auth scopes before accessing the resource. Redirect to the configured
    login_url if one is set, or to redirect_url if one is given.

    Args:
        scopes (str | Sequence[str]): Auth scopes to verify the user has. Defaults to [].
        redirect_url (Optional[str]): Redirect to this url rather than the configured
            login_url.
    """
    scopes_list = [scopes] if isinstance(scopes, str) else list(scopes)

    def decorator(
        func: t.Callable[_P, t.Any],
    ) -> t.Callable[..., t.Awaitable[t.Any]]:
        # Handle async request/response functions.
        @functools.wraps(func)
        async def wrapper(
            request: t.Union[Request, t.Any], *args: _P.args, **kwargs: _P.kwargs
        ) -> t.Any:
            if not isinstance(request, Request):
                raise Exception(
                    "The Request must be the first argument to the function when using the `@requires` decorator"
                )
            if not await _check_session_auth(request, scopes_list):
                REDIRECT_URL = redirect_url if redirect_url else Config.LOGIN_URL
                return RedirectResponse(REDIRECT_URL, 302)
            if isinstance(func, t.Awaitable):  # type: ignore [unused-ignore]
                return await func(request, *args, **kwargs)
            else:
                return func(request, *args, **kwargs)  # type: ignore

        return wrapper

    return decorator


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
    persist_session: bool = True,
    **kwargs: t.Any,
) -> t.Optional[AuthSessionData]:
    """Login user and create an authenticated session.

    Args:
        request (Request): the request
        auth_handler (type[BaseAuth], optional): Auth class to login with.
            Defaults to the default auth handler configured using set_auth_handler().
        persist_session (bool): maintain the session cookie until the maximum age defined
            in the USER_SESSION_EXPIRES environment variable. If false, the cookie is set to
            expire at the end of the browser session. Default True.

    Returns:
        AuthSessionData: The data set on the session. None if invalid login.
    """
    if not auth_handler:
        auth_handler = _AuthConfig.auth_handlers[_AuthConfig.get_default_handler()]
    handler = auth_handler()
    result = await handler.authenticate(request, **kwargs)
    if not result:
        return None
    request.user.update(result)
    if not persist_session:
        request.user["persist_session"] = True
    return result


def logout(request: Request) -> None:
    """Expire the current user session."""
    request.user.clear()
