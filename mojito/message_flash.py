from __future__ import annotations

import json
import typing
from base64 import b64decode

import itsdangerous
from itsdangerous.exc import BadSignature
from starlette.datastructures import Secret
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Receive, Scope, Send

from . import config
from .globals import g


class MessageFlashMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        secret_key: str | Secret = config.Config.SECRET_KEY,
        path: str = "/",
        same_site: typing.Literal["lax", "strict", "none"] = "lax",
        https_only: bool = False,
        domain: str | None = None,
    ) -> None:
        self.app = app
        self.signer = itsdangerous.TimestampSigner(str(secret_key))
        self.message_flash_cookie = config.Config.MESSAGE_FLASH_COOKIE
        self.max_age = 60 * 60  # 1 hr
        self.path = path
        self.security_flags = "httponly; samesite=" + same_site
        if https_only:  # Secure flag can be used with HTTPS only
            self.security_flags += "; secure"
        if domain is not None:
            self.security_flags += f"; domain={domain}"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        connection = HTTPConnection(scope)

        # Read flash messages if the cookie exists and set g.flash_messages
        if self.message_flash_cookie in connection.cookies:
            data = connection.cookies[self.message_flash_cookie].encode("utf-8")

            try:
                data = self.signer.unsign(data, max_age=self.max_age)
                g.flash_messages = json.loads(b64decode(data))
            except BadSignature:
                g.flash_messages = []
        else:
            g.flash_messages = []

        await self.app(scope, receive, send)
