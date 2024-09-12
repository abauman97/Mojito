from asyncio import sleep

from mojito import (
    AppRouter,
    Jinja2Templates,
    JSONResponse,
    Mojito,
    Request,
    auth,
)

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
protected_subrouter = AppRouter("/protected")
protected_subrouter.add_middleware(auth.AuthMiddleware)


@protected_subrouter.route("/")
def protected_route():
    return "<p>protected</p>"


class PasswordAuth(auth.BaseAuth):
    "Authenticate with username and password"

    async def authenticate(self, request: Request, **kwargs: dict[str, str]):
        await sleep(0.5)
        auth_data = auth.AuthSessionData(
            is_authenticated=True,
            user={"id": 1, "name": "Test User", "email": "test@email.com"},
            permissions=["admin"],
        )
        return auth_data


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
