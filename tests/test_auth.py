from mojito import AppRouter, Mojito, Request, auth
from mojito.testclient import TestClient

from .db import get_db

app = Mojito()
protected_router = AppRouter()
protected_router.add_middleware(auth.AuthMiddleware)

client = TestClient(app)


class PasswordAuth(auth.BaseAuth):
    "Authenticate with username and password"

    async def authenticate(self, request: Request, **kwargs: dict[str, str]):
        email: str = kwargs.get("username")  # type:ignore
        password: str = kwargs.get("password")  # type:ignore
        assert email
        assert password
        async with get_db() as db:
            user = await (
                await db.execute(f"SELECT * FROM users where email = '{email}'")
            ).fetchone()
        if not user:
            raise ValueError("No user found in database")
        if not auth.hash_password(password) == user["password"]:
            return None
        user_dict = dict(user)
        del user_dict["password"]
        auth_data = auth.AuthSessionData(
            is_authenticated=True,
            auth_handler="PasswordAuth",
            user_id=user["id"],
            user=dict(user),
            permissions=["admin"],
        )
        return auth_data

    async def get_user(self, user_id: int) -> auth.AuthSessionData:
        async with get_db() as db:
            user = await (
                await db.execute(
                    f"SELECT id, name, email, is_active FROM users where id = {user_id}"
                )
            ).fetchone()
        if not user:
            raise ValueError("No user found in database")
        return auth.AuthSessionData(
            is_authenticated=True,
            auth_handler="PasswordAuth",
            user_id=user["id"],
            user=dict(user),
            permissions=["admin"],
        )


auth.include_auth_handler(PasswordAuth, primary=True)


class TokenAuth(auth.BaseAuth):
    async def authenticate(self, request: Request, **kwargs: dict[str, str]):
        token: str = kwargs.get("token")  # type:ignore
        # Doesn't do anything with the token. Just immitates another auth method
        result = await self.get_user(1)
        return result

    async def get_user(self, user_id: int) -> auth.AuthSessionData:
        password_auth = PasswordAuth()
        result = await password_auth.get_user(user_id)
        result["auth_handler"] = "TokenAuth"
        return result


auth.include_auth_handler(TokenAuth)


@protected_router.route("/login", methods=["GET", "POST"])
async def protected_login_route(request: Request):
    if request.method == "POST":
        await auth.login(request, username="test@email.com", password="password")
        return "login success"
    return "login page"


@protected_router.route("/protected")
def protected_route():
    return "accessed"


@protected_router.route("/login-token", methods=["GET", "POST"])
async def login_token(request: Request):
    # Login using token authentication method
    if request.method == "POST":
        await auth.login(request, TokenAuth, token="random_token")
        return "token login success"
    return "token login page"


app.include_router(protected_router)


def test_route_protection():
    client.cookies.clear()
    result = client.get("/protected")
    assert result.status_code == 200  # Redirects to login page
    assert result.text != "accessed"
    assert result.text == "login page"
    result = client.post("/login")
    assert result.status_code == 200
    result = client.get("/protected")
    assert result.status_code == 200
    assert result.text == "accessed"


def test_secondary_auth_method():
    print("testing secondary auth method")
    client.cookies.clear()
    result = client.get("/protected")
    assert result.status_code == 200
    assert result.text == "login page"
    result = client.post("/login-token")
    assert result.status_code == 200
    result = client.get("/protected")
    assert result.status_code == 200
    assert result.text == "accessed"


scope_protected_router = AppRouter()
scope_protected_router.add_middleware(auth.AuthMiddleware, allow_permissions=["admin"])


@scope_protected_router.route("/scope_protected_admin")
async def scope_protected_admin():
    return "scope protected admin"


invalid_scope_protected_router = AppRouter()
invalid_scope_protected_router.add_middleware(
    auth.AuthMiddleware, allow_permissions=["nope"]
)


@invalid_scope_protected_router.route("/invalid_scope_protected")
async def invalid_scope_protected():
    return "Invalid route"


app.include_router(scope_protected_router)
app.include_router(invalid_scope_protected_router)


def test_valid_scope_protected_router():
    client.cookies.clear()
    result = client.get("/scope_protected_admin")
    assert result.status_code == 200
    assert result.text == "login page"
    result = client.post("/login")
    assert result.status_code == 200
    result = client.get("/scope_protected_admin")
    assert result.status_code == 200
    assert result.text == "scope protected admin"


def test_invalid_scope_protected_router():
    client.cookies.clear()
    result = client.get("/invalid_scope_protected")
    assert result.status_code == 200
    assert result.text == "login page"
    result = client.post("/login")
    assert result.status_code == 200
    result = client.get("/invalid_scope_protected")
    assert result.status_code == 200
    assert result.text == "login page"


@app.route("/decorator_protected")
@auth.require_auth()
def decorator_protected_route():
    return "decorator protected"


def test_decorator_protected():
    client.cookies.clear()  # Clear cookies
    result = client.get("/decorator_protected")
    assert result.status_code == 200  # Redirect to login page
    assert result.text != "decorator protected"
    assert result.text == "login page"
    result = client.post("/login")
    assert result.status_code == 200
    result = client.get("/decorator_protected")
    assert result.status_code == 200
    assert result.text == "decorator protected"


@app.route("/decorator_protected_with_scope")
@auth.require_auth(allow_permissions=["admin"])
def decorator_protected_with_scopes():
    return "decorator protected with scope"


@app.route("/decorator_protected_missing_scope")
@auth.require_auth(allow_permissions=["nope"])
def decorator_protected_missing_scope():
    return "decorator protected missing scope"


def test_decorator_protected_with_scope():
    client.cookies.clear()  # Clear cookies
    result = client.get("/decorator_protected_with_scope")
    assert result.status_code == 200  # Redirect to login page
    assert result.text != "decorator protected with scope"
    assert result.text == "login page"
    result = client.post("/login")
    assert result.status_code == 200
    result = client.get("/decorator_protected_with_scope")
    assert result.text == "decorator protected with scope"


def test_decorator_protected_missing_scope():
    client.cookies.clear()  # Clear cookies
    result = client.get("/decorator_protected_missing_scope")
    assert result.status_code == 200  # Redirect to login page
    assert result.text != "decorator protected missing scope"
    assert result.text == "login page"
    result = client.post("/login")
    assert result.status_code == 200
    result = client.get("/decorator_protected_missing_scope")
    assert result.text != "decorator protected missing scope"
    assert result.text == "login page"


@app.route("/logout", methods=["POST"])
def logout(request: Request):
    auth.logout(request)


def test_logout():
    result = client.post("/login")
    assert result.status_code == 200
    result = client.get("/protected")
    assert result.status_code == 200
    result = client.post("/logout")
    assert result.status_code == 200
    result = client.get("/protected")
    assert result.status_code == 200
    assert result.text == "login page"


scope_admin_protected_router = AppRouter()
scope_admin_protected_router.add_middleware(
    auth.AuthMiddleware, allow_permissions=["admin"]
)


@scope_admin_protected_router.route("/scope_admin_protected_route")
def scope_admin_protected_route():
    return "scope_admin_protected_route"


scope_invalid_protected_router = AppRouter()
scope_invalid_protected_router.add_middleware(
    auth.AuthMiddleware, allow_permissions=["invalid"]
)


@scope_invalid_protected_router.route("/scope_invalid_protected_route")
def scope_invalid_protected_route():
    return "scope_invalid_protected_route"


app.include_router(scope_admin_protected_router)
app.include_router(scope_invalid_protected_router)


def test_auth_required_middleware_scopes():
    result = client.post("/login")
    assert result.status_code == 200
    result = client.get("/scope_admin_protected_route")
    assert result.status_code == 200
    result = client.get("/scope_invalid_protected_route")
    assert result.status_code == 200
    assert result.text == "login page"  # Redirected to login page
