from mojito.mojito.main import (
    AppRouter,
    Request,
    HTMLResponse,
    g,
    flash_message,
    get_flashed_messages,
)
from time import time


router = AppRouter()


@router.route("/")
async def new_route(request: Request):
    flash_message(str(int(time())))
    return f"<h3>Hello, {get_flashed_messages()} with id: {id}</h3>"
