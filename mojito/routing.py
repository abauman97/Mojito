import inspect
from collections.abc import Awaitable, Mapping, Sequence
from typing import Any, Callable, Optional, Union

from starlette.applications import P
from starlette.background import BackgroundTask
from starlette.datastructures import URL
from starlette.middleware import Middleware, _MiddlewareClass  # type: ignore
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response
from starlette.routing import PARAM_REGEX, BaseRoute, Route, Router
from starlette.types import AppType, Lifespan

from . import helpers
from .config import Config
from .globals import g

RouteFunctionType = Callable[[Request], Union[Awaitable[Response], Response]]


class AppRouter(Router):
    def __init__(
        self,
        prefix: Optional[str] = None,
        name: Optional[str] = None,
        middleware: Optional[Sequence[Middleware]] = None,
        routes: Optional[list[BaseRoute]] = None,
        lifespan: Optional[Lifespan[AppType]] = None,
    ) -> None:
        super().__init__(routes=routes, lifespan=lifespan)
        self.middleware = [] if middleware is None else list(middleware)
        self.prefix = prefix or ""
        self.routes: list[BaseRoute] = []
        self.name = name if name else ""

    def include_router(self, router: "AppRouter"):
        for route in router.routes:
            self.routes.append(route)

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
        methods: Optional[list[str]] = None,
        name: Optional[str] = None,
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
                middleware=self.middleware,  # Added to the route if not mounting
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
        methods: Optional[list[str]] = ["GET"],
        name: Optional[str] = None,
        include_in_schema: bool = True,
    ) -> Callable[[Callable[..., Any]], RouteFunctionType]:
        def decorator(
            func: Callable[..., Union[Awaitable[Any], Any]],
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


def redirect_to(
    url: Union[str, URL],
    status_code: int = 302,
    headers: Optional[Mapping[str, str]] = None,
    background: Optional[BackgroundTask] = None,
):
    return RedirectResponse(url, status_code, headers, background)
