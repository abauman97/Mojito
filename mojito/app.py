from typing import (
    Any,
    Callable,
    Mapping,
    Sequence,
    Awaitable,
    AsyncContextManager,
    Union,
    Optional,
)
from starlette.applications import Starlette, AppType
from starlette.middleware import Middleware
from starlette.routing import BaseRoute, Mount
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from starlette.websockets import WebSocket
from .globals import GlobalsMiddleware, g
from .middleware.sessions import SessionMiddleware
from starlette.background import BackgroundTask
from .message_flash import MessageFlashMiddleware
from .routing import AppRouter


RouteFunctionType = Callable[[Request], Union[Awaitable[Response], Response]]


class Mojito(Starlette):
    def __init__(
        self: AppType,
        debug: bool = False,
        routes: Optional[Sequence[BaseRoute]] = None,
        middleware: Optional[Sequence[Middleware]] = None,
        exception_handlers: Optional[
            Mapping[
                Any,
                Union[
                    Callable[
                        [Request, Exception], Union[Response, Awaitable[Response]]
                    ],
                    Callable[[WebSocket, Exception], Awaitable[None]],
                ],
            ]
        ] = None,
        on_startup: Optional[Sequence[Callable[[], Any]]] = None,
        on_shutdown: Optional[Sequence[Callable[[], Any]]] = None,
        lifespan: Optional[
            Union[
                Callable[[AppType], AsyncContextManager[None]],
                Callable[[AppType], AsyncContextManager[Mapping[str, Any]]],
            ]
        ] = None,
    ) -> None:
        super().__init__(
            debug,
            routes,
            middleware,
            exception_handlers,
            on_startup,
            on_shutdown,
            lifespan,
        )
        self.add_middleware(GlobalsMiddleware)
        self.add_middleware(SessionMiddleware)
        self.add_middleware(MessageFlashMiddleware)

    def include_router(self, router: AppRouter):
        """Mounts all the routers routes under the application with the prefix.

        Args:
            router (AppRouter): Instance of the AppRouter
        """
        routes = [route for route in router.routes]
        # Mount router as subapplication
        self.routes.append(
            Mount(path=router.prefix, routes=routes, middleware=router.middleware)
        )
        # for route in router.routes:
        #     self.routes.append(route)


def request() -> Request:
    return g.request


def redirect_to(
    url: str,
    status_code: int = 302,
    headers: Optional[Mapping[str, str]] = None,
    background: Optional[BackgroundTask] = None,
):
    return RedirectResponse(url, status_code, headers, background)
