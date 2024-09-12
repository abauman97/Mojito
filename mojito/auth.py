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


class AuthMiddleware:
    """Uses sessions to authorize and authenticate users with requests.
    Redirect to login_url if session is not authenticated or if user does not have the required auth scopes.
    Can be applied at the app level or on individual routers.

    Will ignore the Config.LOGIN_URL path to prevent infinite redirects.

    Args:
        ignore_routes (Optional[list[str]]): defaults to None. paths of routes to ignore validation on like '/login'. Path should be relative
            and match the Request.url.path value when the route is called.
        require_scopes (Optional[list[str]]): defaults to None. List of scopes the user must have in order to be authorized
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
            is_authenticated: t.Optional[bool] = request.session.get("is_authenticated")
            if not is_authenticated:
                response = RedirectResponse(Config.LOGIN_URL, 302)
                return await response(scope, receive, send)
            # Check that the user has the required scopes
            permissions = request.session.get("permissions", [])
            for allow_permission in self.allow_permissions:
                if not allow_permission in permissions:
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
        def requires_auth_function(*args: t.Any, **kwargs: dict[str, t.Any]):
            request = g.request
            assert isinstance(request, Request)
            REDIRECT_URL = redirect_url if redirect_url else Config.LOGIN_URL
            if not request.session.get("is_authenticated", False):
                return RedirectResponse(REDIRECT_URL, 302)
            permissions = request.session.get("permissions", [])
            for allow_permission in allow_permissions:
                if not allow_permission in permissions:
                    return RedirectResponse(REDIRECT_URL, 302)
            return func(*args, **kwargs)

        return requires_auth_function

    return wrapper


class AuthSessionData(t.TypedDict):
    is_authenticated: bool
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
    auth_handler: type[BaseAuth],
    **kwargs: t.Any,
):
    handler = auth_handler()
    result = await handler.authenticate(request, **kwargs)
    if not result:
        return False
    request.session.update(result)
    return result


def logout(request: Request):
    """Expire the current user session."""
    request.session.clear()
