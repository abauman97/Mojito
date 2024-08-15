"Configure routes for testing"
from mojito import Mojito, AppRouter, Response, Request

app = Mojito()

router = AppRouter()

app.include_router(router)


@router.route("/")
def test_route():
    return "Hello World"


def non_decorated_route(request: Request):
    return Response("Hello World")


router.add_route("/non_decorated_route", non_decorated_route)
