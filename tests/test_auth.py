from mojito import Mojito, AppRouter, auth, Request
from mojito.testclient import TestClient
from .main import PasswordAuth

app = Mojito()
protected_router = AppRouter()
protected_router.add_middleware(auth.LoginRequiredMiddleware)
client = TestClient(app)
auth.add_auth_handler(PasswordAuth)


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
