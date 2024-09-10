"""Authentication and authorization utilities to reduce the boilerplate required to implement basic session
based authentication."""

import abc
import functools
import hashlib
import typing as t

from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .config import Config
from .globals import g


class AuthRequiredMiddleware:
    """Redirect to login_url if session is not authenticated or if user does not have the required auth scopes.
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
        require_scopes: t.Optional[list[str]] = None,
    ) -> None:
        self.app = app
        self.ignore_routes = ignore_routes
        self.require_scopes = require_scopes

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
            user_scopes = request.session.get("user_scopes", [])
            for required_scope in self.require_scopes if self.require_scopes else []:
                if not required_scope in user_scopes:
                    response = RedirectResponse(Config.LOGIN_URL, 302)
                    return await response(scope, receive, send)
            await send(message)

        await self.app(scope, receive, send_wrapper)


def require_auth(
    scopes: t.Optional[list[str]] = None, redirect_url: t.Optional[str] = None
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
            if scopes:
                user_scopes = request.session.get("user_scopes", [])
                for required_scope in scopes:
                    if not required_scope in user_scopes:
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
    user_scopes: t.Optional[list[str]]
    "user_scopes are used to authorize the user. Think of them as roles or permissions."


class BaseAuth:
    """Base class that all authentication methods should implement.

    Subclasses must implement authorize() and authenticate() methods.
    """

    @abc.abstractmethod
    async def authorize(self, request: Request, scopes: list[str]) -> bool:
        """Method to check if the user has the required scopes. The user must have all
        scopes given to be valid.

        Args:
            scopes (list[str]): list of scopes to check check that the user has.

        Raises:
            NotImplementedError: Method not implemented.

        Returns:
            bool: User is authorized
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def authenticate(
        self, request: Request, username: str, password: str
    ) -> t.Optional[AuthSessionData]:
        """Method to authenticate the user based on the users username and password. Will
        be used by the password_login() function to authenticate the user.

        Args:
            request (Request): Mojito/Starlette request object
            username (str): The users username
            password (str): The users password in plain text. Stored passwords should be
                hashed and compared to check validity. This module provides the hash_password()
                function to easily compare the hashed vs the given password.

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


class AuthConfig:
    """Global configuration options for auth functionality."""

    auth_handler: t.Optional[type[BaseAuth]] = None


def set_auth_handler(handler: type[BaseAuth]):
    """Set and auth handler to the AuthConfig.auth_handler setting. Only one auth handler can
    be set at a time. Setting an auth handler will override any set previously.

    Args:
        handler (type[BaseAuth]): The auth handler class that implements the BaseAuth class
    """
    AuthConfig.auth_handler = handler


async def password_login(username: str, password: str):
    """Login user based on username and password. Authenticates user and sets data on the
    session object. Uses the `authenticate` function from AuthHandler configured on the
    AuthConfig.auth_handler class. Use the function `set_auth_handler` to configure an
    AuthHandler.

    Args:
        username (str): The username to identify the user
        password (str): The users plain text password. Will be compared to the hashed version in storage.
    """
    request: Request = g.request
    if not AuthConfig.auth_handler:
        raise NotImplementedError(
            "an auth handler must be defined to use password_login"
        )
    auth = AuthConfig.auth_handler()  # Get Auth class from config
    result = await auth.authenticate(
        request=request, username=username, password=password
    )
    if not result:
        return False
    request.session.update(result)
    return result.get("is_authenticated", False)


def logout():
    """Expire the current user session."""
    request: Request = g.request
    assert request, "unable to access g.request"
    request.session.clear()
