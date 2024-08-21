from mojito import (
    AppRouter,
    Request,
    HTMLResponse,
    g,
    flash_message,
    get_flashed_messages,
    Jinja2Templates,
    redirect_to,
)
from mojito import auth
from time import time


router = AppRouter()

router.add_middleware(auth.LoginRequiredMiddleware)


@router.route("/{id:int}")
async def id_route(id: int, filter_str: str, request: Request):
    print(f"request.base_url: {request.base_url}")
    flash_message(str(int(time())))
    return f"<h3>Hello, {get_flashed_messages()} with id: {filter_str}</h3>"


templates = Jinja2Templates("tests/templates")


@router.route("/login", methods=["GET", "POST"])
async def login(request: Request):
    if request.method == "GET":
        return templates.TemplateResponse(
            request=request, name="login.jinja", context={"g": g}
        )
    form = await request.form()
    email = form.get("email")
    password = form.get("password")
    if not email or not password:
        flash_message("Email or password missing")
    flash_message(f"Email: {email}")
    flash_message(f"password: {password}")
    success = await auth.password_login(email, password)
    return redirect_to("/")


@router.route("/login2", methods=["GET", "POST"])
async def login2(request: Request):
    return await login(request)
