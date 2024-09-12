from typing import Any

from mojito import (
    AppRouter,
    Jinja2Templates,
    JSONResponse,
    Mojito,
    Request,
    auth,
)

from .db import get_db

app = Mojito()

templates = Jinja2Templates("tests/templates")

main_router = AppRouter()


@main_router.route("/")
async def index():
    return "index_response"


@main_router.route("/async_route")
async def async_route():
    return "async_route_response"


@main_router.route("/{id:int}")
async def id_route_with_query_params(id: int, query_param_1: str, request: Request):
    return JSONResponse({"id": id, "query_param_1": query_param_1})


# TEST PROTECTED ROUTES
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

    async def get_user(self, user_id: Any) -> auth.AuthSessionData:
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


auth.include_auth_handler(PasswordAuth)

protected_subrouter = AppRouter("/protected")
protected_subrouter.add_middleware(auth.AuthMiddleware)


@protected_subrouter.route("/")
def protected_route():
    return "<p>protected</p>"


@app.route("/app-route")
def app_route():
    return "app-route"


main_router.include_router(protected_subrouter)

app.include_router(main_router)

if __name__ == "__main__":
    import uvicorn

    for route in app.routes:
        print(f"route: {route}")
    uvicorn.run("tests.main:app", reload=True)
