from collections.abc import Awaitable, Mapping, Sequence
from contextlib import AbstractAsyncContextManager
from typing import (
    Any,
    Callable,
    Optional,
    Union,
)

from starlette.applications import AppType, Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute
from starlette.websockets import WebSocket

from .globals import GlobalsMiddleware
from .message_flash import MessageFlashMiddleware
from .middleware.sessions import SessionMiddleware
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
                Callable[[AppType], AbstractAsyncContextManager[None]],
                Callable[[AppType], AbstractAsyncContextManager[Mapping[str, Any]]],
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
        self.router = AppRouter(lifespan=lifespan)
        self.add_middleware(GlobalsMiddleware)
        self.add_middleware(SessionMiddleware)
        self.add_middleware(MessageFlashMiddleware)

    def include_router(self, router: AppRouter):
        """Mounts all the routers routes under the application with the prefix.

        Args:
            router (AppRouter): Instance of the AppRouter
        """
        self.router.include_router(router)

    def route(
        self,
        path: str,
        methods: Optional[list[str]] = ["GET"],
        name: Optional[str] = None,
        include_in_schema: bool = True,
    ):
        return self.router.route(
            path=path, methods=methods, name=name, include_in_schema=include_in_schema
        )
