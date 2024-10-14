from __future__ import annotations

import datetime
import json
import typing
from base64 import b64decode, b64encode

import itsdangerous
from itsdangerous.exc import BadSignature
from starlette.datastructures import MutableHeaders
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .. import config

if typing.TYPE_CHECKING:
    from ..auth import AuthSessionData


class UserSessionMiddleware:
    """Adds `user` data to the Request object.

    Used for authentication and session management.
    """

    # Works nearly the same as Starlettes SessionMiddleware but without some of the configuration options
    def __init__(
        self,
        app: ASGIApp,
        same_site: typing.Literal["lax", "strict", "none"] = "strict",
        https_only: bool = False,
        domain: str | None = None,
    ) -> None:
        self.app = app
        self.signer = itsdangerous.TimestampSigner(config.Config.SECRET_KEY)
        self.cookie_name = config.Config.USER_SESSION_COOKIE
        self.max_age = config.Config.USER_SESSION_EXPIRES
        self.path = "/"
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
        initial_user_was_empty = True

        if self.cookie_name in connection.cookies:
            # RECEIVE COOKIE
            data = connection.cookies[self.cookie_name].encode("utf-8")
            try:
                data_bytes, timestamp = self.signer.unsign(
                    data, max_age=self.max_age, return_timestamp=True
                )
                data_decoded = b64decode(data_bytes)
                json_data: AuthSessionData = json.loads(data_decoded)
                reauthenticate_after = timestamp + datetime.timedelta(
                    seconds=config.Config.USER_SESSION_REVALIDATE_AFTER
                )
                if datetime.datetime.now(datetime.timezone.utc) > reauthenticate_after:
                    json_data["is_authenticated"] = (
                        False  # Force reauthentication if session needs revalidated
                    )
                scope["user"] = json_data
                initial_user_was_empty = False
            except BadSignature:
                scope["user"] = {}
        else:
            scope["user"] = {}

        async def send_wrapper(message: Message) -> None:
            # SEND COOKIE
            if message["type"] == "http.response.start":
                if scope["user"]:
                    # We have user data to persist.
                    data = b64encode(json.dumps(scope["user"]).encode("utf-8"))
                    data = self.signer.sign(data)
                    headers = MutableHeaders(scope=message)
                    header_value = "{cookie_name}={data}; path={path}; {max_age}{security_flags}".format(  # noqa E501
                        cookie_name=self.cookie_name,
                        data=data.decode("utf-8"),
                        path=self.path,
                        max_age=f"Max-Age={self.max_age}; "
                        if scope["user"].get("persist_session", False)
                        else "",
                        security_flags=self.security_flags,
                    )
                    headers.append("Set-Cookie", header_value)
                elif not initial_user_was_empty:
                    # The user has been cleared.
                    headers = MutableHeaders(scope=message)
                    header_value = "{cookie_name}={data}; path={path}; {expires}{security_flags}".format(  # noqa E501
                        cookie_name=self.cookie_name,
                        data="null",
                        path=self.path,
                        expires="expires=Thu, 01 Jan 1970 00:00:00 GMT; ",
                        security_flags=self.security_flags,
                    )
                    headers.append("Set-Cookie", header_value)
            await send(message)

        await self.app(scope, receive, send_wrapper)
