import os
import typing
from asyncio import AbstractEventLoop
from os import PathLike

import jinja2
from starlette.background import BackgroundTask
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import _TemplateResponse  # type: ignore[unused-ignore]

from mojito.config import Config

_TEMPLATES_DIR = os.path.join(Config.ROOT_DIR, Config.TEMPLATES_DIRECTORY)


class BlockNotFoundError(Exception):
    def __init__(
        self, block_name: str, template_name: str, message: typing.Optional[str] = None
    ):
        self.block_name = block_name
        self.template_name = template_name
        super().__init__(
            message
            or f"Block {self.block_name!r} not found in template {self.template_name!r}"
        )


def _render_template_blocks(
    environment: jinja2.Environment,
    template_name: str,
    block_names: list[str],
    *args: typing.Any,
    **kwargs: typing.Any,
) -> str:
    contents: list[str] = []
    template = environment.get_template(template_name)

    for block_name in block_names:
        try:
            block_render_func = template.blocks[block_name]
        except KeyError:
            raise BlockNotFoundError(block_name, template_name)

        ctx = template.new_context(dict(*args, **kwargs))
        try:
            contents.append(environment.concat(block_render_func(ctx)))  # type: ignore
        except Exception:
            environment.handle_exception()
    return "".join(contents)


async def _render_template_blocks_async(
    environment: jinja2.Environment,
    template_name: str,
    block_names: list[str],
    *args: typing.Any,
    **kwargs: typing.Any,
) -> str:
    if not environment.is_async:
        raise RuntimeError("The environment was not created with async mode enabled.")

    contents: list[str] = []
    template = environment.get_template(template_name)

    for block_name in block_names:
        try:
            block_render_func = template.blocks[block_name]
        except KeyError:
            raise BlockNotFoundError(block_name, template_name)

        ctx = template.new_context(dict(*args, **kwargs))
        try:
            contents.append(
                environment.concat([n async for n in block_render_func(ctx)])  # type: ignore
            )
        except Exception:
            environment.handle_exception()
    return "".join(contents)


def _get_loop() -> tuple[AbstractEventLoop, bool]:
    import asyncio

    close = False

    try:
        return (asyncio.get_running_loop(), close)
    except RuntimeError:
        close = True
        return (asyncio.new_event_loop(), close)


async def _render_blocks_async(
    environment: jinja2.Environment,
    template_name: str,
    block_names: list[str],
    *args: typing.Any,
    **kwargs: typing.Any,
) -> str:
    """
    This works similar to :func:`render_blocks` but returns a coroutine that when
    awaited returns every rendered template block as a single string. This requires
    the environment async feature to be enabled.
    """
    if not environment.is_async:
        raise RuntimeError("The environment was not created with async mode enabled.")

    return await _render_template_blocks_async(
        environment, template_name, block_names, *args, **kwargs
    )


def _render_blocks(
    environment: jinja2.Environment,
    template_name: str,
    block_names: list[str],
    *args: typing.Any,
    **kwargs: typing.Any,
) -> str:
    """This returns one or more rendered template blocks as a string."""
    if environment.is_async:
        loop, close = _get_loop()

        try:
            return loop.run_until_complete(
                _render_blocks_async(
                    environment, template_name, block_names, *args, **kwargs
                )
            )
        finally:
            if close:
                loop.close()

    return _render_template_blocks(
        environment, template_name, block_names, *args, **kwargs
    )


class Templates:
    """
    templates = Templates("templates")

    return templates.TemplateResponse(request, "index.html")
    """

    def __init__(
        self,
        directory: typing.Union[
            str, PathLike[str], typing.Sequence[typing.Union[str, PathLike[str]]], None
        ] = None,
        *,
        context_processors: typing.Optional[
            list[typing.Callable[[Request], dict[str, typing.Any]]]
        ] = None,
        env: typing.Optional[jinja2.Environment] = None,
    ) -> None:
        """The base class to use jinja2 templates in your application.

        Args:
            directory (str | PathLike[str] | typing.Sequence[str | PathLike[str]] | None, optional): The templates directory on the file system.
                Can be relative or absolute. Defaults to None.
            context_processors (list[typing.Callable[[Request], dict[str, typing.Any]]] | None, optional): Defaults to None.
            env (jinja2.Environment | None, optional): A preconfigured jinja2.Environment. Will be ignored if directory is not None. Defaults to None.

        When neither a directory or env is given, the directory will default to the templates directory (Config.TEMPLATES_DIRECTORY) relative
        to the root directory (Config.ROOT_DIRECTORY).
        """
        assert jinja2 is not None, "jinja2 must be installed to use Jinja2Templates"
        if not directory and not env:
            directory = _TEMPLATES_DIR
        # assert bool(directory) ^ bool(
        #     env
        # ), "either 'directory' or 'env' arguments must be passed"
        self.context_processors = context_processors or []
        if directory is not None:
            self.env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(directory), autoescape=True
            )
        elif env is not None:
            self.env = env

        self._setup_env_defaults(self.env)

    def _setup_env_defaults(self, env: jinja2.Environment) -> None:
        @jinja2.pass_context
        def url_for(
            context: dict[str, typing.Any],
            name: str,
            /,
            **path_params: typing.Any,
        ) -> URL:
            request: Request = context["request"]
            return request.url_for(name, **path_params)

        env.globals.setdefault("url_for", url_for)  # type: ignore[unused-ignore]

    def get_template(self, name: str) -> jinja2.Template:
        return self.env.get_template(name)

    def TemplateResponse(
        self,
        request: Request,
        name: str,
        context: dict[str, typing.Any],
        status_code: int = 200,
        headers: typing.Optional[typing.Mapping[str, str]] = None,
        media_type: typing.Optional[str] = None,
        background: typing.Optional[BackgroundTask] = None,
        block: typing.Optional[typing.Union[str, list[str]]] = None,
    ) -> HTMLResponse:
        """Render the template and return it as an HTMLResponse.

        Args:
            request (Request): the Request object.
            name (str): Name of the template relative to the configured templates directory.
            context (dict[str, Any]): Optional dict to add to the templates render context.
            status_code (int, optional): Response status code. Defaults to 200.
            headers (Mapping[str, str], optional): Headers included in the response. Defaults to None.
            media_type (str, optional): Defaults to None.
            background (BackgroundTask, optional): Defaults to None.
            block (str | list[str], optional): The name of the template block/partial to render. If None
                the entire template will be rendered. Defaults to None.

        Returns:
            Response: HTML response of full or partial(block) template.
        """
        template = self.get_template(name)

        blocks: typing.Optional[list[str]] = None
        if isinstance(block, list):
            blocks = block
        elif block:
            blocks = [block]

        if blocks:
            content = _render_blocks(
                self.env,
                name,
                blocks,
                context,
            )
            return HTMLResponse(
                content=content,
                status_code=status_code,
                headers=headers,
                media_type=media_type,
                background=background,
            )

        return _TemplateResponse(
            template,
            context,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )
