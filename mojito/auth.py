"Authentication and authorization handlers built off of sessions and scoped to the request to allow for database lookups"

# A common need is to validate a session cookie and perform a database lookup to validate
# the user. This is not a middlware so that the current request can be included in the handler functions
import abc
import hashlib
import typing as t

from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .config import Config
from .globals import g


class LoginRequiredMiddleware:
    """Redirect to login_url if session is not authenticated. Can be applied at the app level
    or on individual routers.

    Will ignore the Config.LOGIN_URL path to prevent infinite redirects.

    Args:
        ignore_routes (list[str]): paths of routes to ignore validation on like '/login'. Path should be relative
            and match the Request.url.path value when the route is called.
    """

    def __init__(self, app: ASGIApp, ignore_routes: list[str] = []) -> None:
        self.app = app
        self.ignore_routes = ignore_routes

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
            await send(message)

        await self.app(scope, receive, send_wrapper)


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
    ) -> t.Optional[tuple[bool, list[str]]]:
        """Method to authenticate the user based on the users username and password. Will
        be used by the password_login() function to authenticate the user.

        Args:
            request (Request): Mojito/Starlette request object
            username (str): The users username
            password (str): The users password in plain text. Stored passwords should be
                hashed and compared to check validity. This base class provides hash_password()
                static method to easily compare the hashed vs the given password.

        Raises:
            NotImplementedError: Method not implemented

        Returns:
            tuple[bool, list[str]] | None: (is_authenticated: bool, user_scopes: list[str])
        """
        raise NotImplementedError()


def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()


class AuthConfig:
    auth_handler: t.Optional[type[BaseAuth]] = None


def add_auth_handler(handler: type[BaseAuth]):
    AuthConfig.auth_handler = handler


async def password_login(username: str, password: str):
    """Login user based on username and password. Authenticates user and sets data on the
    session object. Uses the

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
    is_authenticated = result[0]
    request.session["is_authenticated"] = is_authenticated
    request.session["auth_scopes"] = result[1]
    return True if is_authenticated else False
