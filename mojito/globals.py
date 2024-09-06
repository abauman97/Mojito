# Credit to https://gist.github.com/ddanier/ead419826ac6c3d75c96f9d89bea9bd0
from collections.abc import Awaitable, Callable
from contextvars import ContextVar, copy_context
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class GlobalContextVar:
    __slots__ = ("_vars", "_defaults")

    _vars: dict[str, ContextVar[Any]]
    _defaults: dict[str, Any]

    def __init__(self) -> None:
        object.__setattr__(self, "_vars", {})
        object.__setattr__(self, "_defaults", {})

    def set_default(self, name: str, default: Any) -> None:
        """Set a default value for a variable."""

        # Ignore if default is already set and is the same value
        if name in self._defaults and default is self._defaults[name]:
            return

        # Ensure we don't have a value set already - the default will have
        # no effect then
        if name in self._vars:
            raise RuntimeError(
                f"Cannot set default as variable {name} was already set",
            )

        # Set the default already!
        self._defaults[name] = default

    def _get_default_value(self, name: str) -> Any:
        """Get the default value for a variable."""

        default = self._defaults.get(name, None)

        return default() if callable(default) else default

    def _ensure_var(self, name: str) -> None:
        """Ensure a ContextVar exists for a variable."""

        if name not in self._vars:
            default = self._get_default_value(name)
            self._vars[name] = ContextVar(f"globals:{name}", default=default)

    def __getattr__(self, name: str) -> Any:
        """Get the value of a variable."""

        self._ensure_var(name)
        return self._vars[name].get()

    def __setattr__(self, name: str, value: Any) -> None:
        """Set the value of a variable."""

        self._ensure_var(name)
        self._vars[name].set(value)


async def globals_middleware_dispatch(
    request: Request,
    call_next: Callable[..., Any],
) -> Response:
    """Dispatch the request in a new context to allow globals to be used."""

    ctx = copy_context()

    def _call_next() -> Awaitable[Response]:
        return call_next(request)

    return await ctx.run(_call_next)


g = GlobalContextVar()
"""
Global context variable similar to Flasks g.

Usage:
    g.foo = "Foo"

    print(g.foo) -> "Foo"
"""


class GlobalsMiddleware(BaseHTTPMiddleware):  # noqa
    """Middleware to setup the globals context using globals_middleware_dispatch().

    Should be the first middleware processed in the application. Sets g.request to the
    current request."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app, globals_middleware_dispatch)
