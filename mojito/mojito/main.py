from typing import (
    Any,
    Callable,
    Mapping,
    Sequence,
    Awaitable,
    AsyncContextManager,
)
from starlette.applications import Starlette, AppType
from starlette.middleware import Middleware
from starlette.routing import BaseRoute, Route
from starlette.requests import Request
from starlette.responses import Response, HTMLResponse
from starlette.websockets import WebSocket
from starlette.templating import Jinja2Templates
from .globals import GlobalsMiddleware, g
from . import message_flashing
from .message_flashing import (
    get_flashed_messages,
    flash_message,
)


RouteFunctionType = Callable[[Request], Awaitable[Response] | Response]


class AppRouter:
    def __init__(
        self, prefix: str | None = None, middleware: Sequence[Middleware] | None = None
    ) -> None:
        self.middleware: Sequence[Middleware] | None = middleware
        self.prefix = prefix or ""
        self.routes: list[Route] = []

    def add_route(
        self,
        path: str,
        endpoint: RouteFunctionType,
        methods: list[str] | None = None,
        name: str | None = None,
        include_in_schema: bool = True,
    ) -> None:
        path = self.prefix + path
        self.routes.append(
            Route(
                path=path,
                endpoint=endpoint,
                methods=methods,
                name=name,
                include_in_schema=include_in_schema,
                middleware=self.middleware,
            )
        )

    def route(
        self,
        path: str,
        methods: list[str] | None = ["GET"],
        include_in_schema: bool = True,
    ) -> Callable[[Callable[[Request], Any]], RouteFunctionType]:

        def decorator(
            func: Callable[[Request], Awaitable[Any] | Any],
        ) -> RouteFunctionType:
            async def func_with_response(
                request: Request, *args: tuple[Any], **kwargs: dict[str, Any]
            ):
                # Check if any flash messages exist
                messages = request.cookies.get("flash_messages")
                if messages:
                    g.flash_messages = message_flashing.decode_message_cookie(messages)

                # Ensures the function has a Response return type.
                response = func(request, *args, **kwargs)
                if isinstance(response, Awaitable):
                    response = await response
                print(
                    f"[main decorator] g.next_flash_messages: {g.next_flash_messages}"
                )
                if not isinstance(response, Response):
                    # Wrap response in default HTMLResponse
                    response = HTMLResponse(str(response))
                if g.next_flash_messages:
                    response.set_cookie(
                        "flash_messages",
                        message_flashing.encode_message_cookie(
                            g.next_flash_message
                        ).decode("utf-8"),
                    )
                return response

            self.add_route(
                path,
                func_with_response,
                methods=methods,
                name=func.__name__,
                include_in_schema=include_in_schema,
            )
            return func_with_response

        return decorator


class Mojito(Starlette):
    def __init__(
        self: AppType,
        debug: bool = False,
        routes: Sequence[BaseRoute] | None = None,
        middleware: Sequence[Middleware] | None = None,
        exception_handlers: (
            Mapping[
                Any,
                Callable[[Request, Exception], Response | Awaitable[Response]]
                | Callable[[WebSocket, Exception], Awaitable[None]],
            ]
            | None
        ) = None,
        on_startup: Sequence[Callable[[], Any]] | None = None,
        on_shutdown: Sequence[Callable[[], Any]] | None = None,
        lifespan: (
            Callable[[AppType], AsyncContextManager[None]]
            | Callable[[AppType], AsyncContextManager[Mapping[str, Any]]]
            | None
        ) = None,
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
        # self.add_middleware(MessageFlashMiddleware, secret_key=Config.SECRET_KEY)

    def include_router(self, router: AppRouter):
        for route in router.routes:
            self.routes.append(route)


# TODO - default path should be base where app is initialized
_templates_default = Jinja2Templates(".")
TemplateResponse = _templates_default.TemplateResponse
"Quick access to Jinja2Templates.TemplateResponse with default template Jinja2 configuration"
