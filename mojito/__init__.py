"""Mojito framework. Fresh, fast, and simple web framework for building HTML-first websites"""

__version__ = "0.1.0a4"

from .app import Mojito as Mojito
from .globals import g as g
from .helpers import (
    flash_message as flash_message,
)
from .helpers import (
    get_flashed_messages as get_flashed_messages,
)
from .requests import Request as Request
from .responses import (
    FileResponse as FileResponse,
)
from .responses import (
    HTMLResponse as HTMLResponse,
)
from .responses import (
    JSONResponse as JSONResponse,
)
from .responses import (
    PlainTextResponse as PlainTextResponse,
)
from .responses import (
    RedirectResponse as RedirectResponse,
)
from .responses import (
    Response as Response,
)
from .responses import (
    StreamingResponse as StreamingResponse,
)
from .routing import AppRouter as AppRouter
from .routing import redirect_to as redirect_to
from .staticfiles import StaticFiles as StaticFiles
from .templating import Jinja2Templates as Jinja2Templates
