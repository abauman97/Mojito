from typing import (
    Any,
    Callable,
    Mapping,
    Sequence,
    Awaitable,
    AsyncContextManager,
)
from starlette.applications import Starlette, AppType, P
from starlette.middleware import Middleware, _MiddlewareClass  # type: ignore
from starlette.routing import BaseRoute, Route, Router, PARAM_REGEX, Mount
from starlette.requests import Request
from starlette.responses import Response, HTMLResponse, RedirectResponse
from starlette.websockets import WebSocket
from starlette.templating import Jinja2Templates
from . import helpers
from .globals import GlobalsMiddleware, g
from .middleware.sessions import SessionMiddleware
from starlette.background import BackgroundTask
from .message_flash import MessageFlashMiddleware
from .config import Config


import inspect


RouteFunctionType = Callable[[Request], Awaitable[Response] | Response]


class AppRouter(Router):
    def __init__(
        self, prefix: str | None = None, middleware: Sequence[Middleware] | None = None
    ) -> None:
        self.middleware = [] if middleware is None else list(middleware)
        self.prefix = prefix or ""
        self.routes: list[Route] = []

    def add_middleware(
        self,
        middleware_class: type[_MiddlewareClass[P]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        """Adds includes middleware within the router.

        Args:
            middleware_class (type[_MiddlewareClass[P]]): ASGI compatible middleware
        """
        self.middleware.insert(0, Middleware(middleware_class, *args, **kwargs))

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
                # middleware=self.middleware,
            )
        )

    def _process_endpoint_args(
        self, request: Request, path: str, endpoint_function: Callable[..., Any]
    ) -> dict[str, Any]:
        """Inspect the endpoint function arguments and inject their values as **kwargs when
        the function is called from the endpoint.

        Args:
            request (Request): starlette.Request
            path (str): route path
            endpoint_function (Callable[..., Any]): The endpoint function

        Returns:
            dict[str, Any]: kwargs to call the endpoint function with
        """
        path_params_tuple = PARAM_REGEX.findall(
            path
        )  # Pull the path params from the path with converter split if it exists
        arg_specs = inspect.getfullargspec(endpoint_function)
        path_params = [p[0] for p in path_params_tuple]  # Extract just param name
        kwargs: dict[str, Any] = {}
        for arg_name, arg_type in arg_specs.annotations.items():
            arg_value: Any | None = None
            if arg_name in path_params:
                # Arguments in path params
                arg_value = request.path_params.get(arg_name)
            elif arg_name == "return":
                # Handle 'return' type if one is included.
                # https://docs.python.org/3/library/inspect.html#inspect.getfullargspec
                # Skip processing 'return' type annotation
                continue
            elif arg_type == Request:
                # Add request to this argument
                arg_value = request
            else:
                # Remaining arguments are treated as query params
                arg_value = request.query_params.get(arg_name)
            kwargs[arg_name] = arg_value
        return kwargs

    def route(
        self,
        path: str,
        methods: list[str] | None = ["GET"],
        name: str | None = None,
        include_in_schema: bool = True,
    ) -> Callable[[Callable[..., Any]], RouteFunctionType]:

        def decorator(
            func: Callable[..., Awaitable[Any] | Any],
        ) -> RouteFunctionType:

            async def endpoint_function(request: Request):
                """Creates a function that inputs the correct arguments to the func at runtime."""
                kwargs = self._process_endpoint_args(request, path, func)
                g.request = request

                # Ensures the function has a Response return type.
                response = func(**kwargs)
                if isinstance(response, Awaitable):
                    response = await response
                if not isinstance(response, Response):
                    # Wrap response in default HTMLResponse
                    response = HTMLResponse(str(response))

                # PROCESS MESSAGE FLASHING FOR NEXT REQUEST
                if g.next_flash_messages:
                    response.set_cookie(
                        Config.MESSAGE_FLASH_COOKIE,
                        helpers.encode_message_cookie(g.next_flash_message).decode(
                            "utf-8"
                        ),
                    )
                return response

            self.add_route(
                path,
                endpoint_function,
                methods=methods,
                name=name if name else func.__name__,
                include_in_schema=include_in_schema,
            )
            return func

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


# TODO - default path should be base where app is initialized
_templates_default = Jinja2Templates(".")
TemplateResponse = _templates_default.TemplateResponse
"Quick access to Jinja2Templates.TemplateResponse with default template Jinja2 configuration"


def request() -> Request:
    return g.request


def redirect_to(
    url: str,
    status_code: int = 302,
    headers: Mapping[str, str] | None = None,
    background: BackgroundTask | None = None,
):
    return RedirectResponse(url, status_code, headers, background)
