"Authentication and authorization handlers built off of sessions and scoped to the request to allow for database lookups"
# A common need is to validate a session cookie and perform a database lookup to validate
# the user. This is not a middlware so that the current request can be included in the handler functions
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.types import ASGIApp, Scope, Send, Receive, Message
from .globals import g
from .config import Config
import hashlib


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
                or request.url.path in Config.LOGIN_URL
            ):
                # Skip for routes registered as login_not_required
                return await send(message)
            is_authenticated: bool | None = request.session.get("is_authenticated")
            if not is_authenticated:
                response = RedirectResponse(Config.LOGIN_URL, 302)
                return await response(scope, receive, send)
            await send(message)

        await self.app(scope, receive, send_wrapper)


class AuthBase:
    "Preconfigured authentication helpers"

    def hash_password(self, password: str):
        return hashlib.sha256(password.encode()).hexdigest()

    async def authorize(self, scopes: list[str]) -> bool:
        "Method to check if the user has the required scopes"
        raise NotImplementedError()

    async def authenticate(
        self, request: Request, username: str, password: str
    ) -> tuple[str, str] | None:
        "Method to be overridden with different authentication methods. Returns a tuple with (is_authenticated: bool, scopes: list[str])"
        raise NotImplementedError()


async def password_login(username: str, password: str):
    """Login user based on username and password. Authenticates user and sets data on the
    session object.

    Args:
        username (str): _description_
        password (str): _description_
    """
    # Use auth handler function to get the is_authenticated and scopes
    request: Request = g.request
    auth = AuthBase()  # Get Auth class from config
    result = await auth.authenticate(
        request=request, username=username, password=password
    )
    if not result:
        return False
    is_authenticated = result[0]
    request.session["is_authenticated"] = is_authenticated
    request.session["auth_scopes"] = result[1]
    return True if is_authenticated else False
