from mojito import AppRouter, Mojito, Request, auth
from mojito.testclient import TestClient

from .main import PasswordAuth

app = Mojito()
protected_router = AppRouter()
protected_router.add_middleware(auth.AuthRequiredMiddleware)

client = TestClient(app)
auth.set_auth_handler(PasswordAuth)


@protected_router.route("/login", methods=["GET", "POST"])
async def protected_login_route(request: Request):
    if request.method == "POST":
        await auth.password_login("username", "password")
        return "login success"
    return "login page"


@protected_router.route("/protected")
def protected_route():
    return "accessed"


app.include_router(protected_router)


def test_route_protection():
    result = client.get("/protected")
    assert result.status_code == 200  # Redirects to login page
    assert result.text != "accessed"
    assert result.text == "login page"
    result = client.post("/login")
    assert result.status_code == 200
    result = client.get("/protected")
    assert result.status_code == 200
    assert result.text == "accessed"


scope_protected_router = AppRouter()
scope_protected_router.add_middleware(
    auth.AuthRequiredMiddleware, require_scopes=["admin"]
)


@scope_protected_router.route("/scope_protected_admin")
async def scope_protected_admin():
    return "scope protected admin"


invalid_scope_protected_router = AppRouter()
invalid_scope_protected_router.add_middleware(
    auth.AuthRequiredMiddleware, require_scopes=["nope"]
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
@auth.require_auth(scopes=["admin"])
def decorator_protected_with_scopes():
    return "decorator protected with scope"


@app.route("/decorator_protected_missing_scope")
@auth.require_auth(scopes=["nope"])
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
def logout():
    auth.logout()


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
    auth.AuthRequiredMiddleware, require_scopes=["admin"]
)


@scope_admin_protected_router.route("/scope_admin_protected_route")
def scope_admin_protected_route():
    return "scope_admin_protected_route"


scope_invalid_protected_router = AppRouter()
scope_invalid_protected_router.add_middleware(
    auth.AuthRequiredMiddleware, require_scopes=["invalid"]
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
