from mojito import (
    AppRouter,
    Request,
    HTMLResponse,
    g,
    flash_message,
    get_flashed_messages,
)
from time import time


router = AppRouter()


# @router.route("/")
# async def index_route():
#     print(f"request().method: {request().method}")
#     flash_message(str(int(time())))
#     return f"<h3>Hello, {get_flashed_messages()}</h3>"


@router.route("/{id:int}")
async def id_route(id: int, filter_str: str, request: Request):
    print(f"request.base_url: {request.base_url}")
    flash_message(str(int(time())))
    return f"<h3>Hello, {get_flashed_messages()} with id: {filter_str}</h3>"
