import json
import typing as t
from base64 import b64encode

import itsdangerous

from .config import Config
from .globals import g


class MessageFlash(t.TypedDict):
    message: str
    category: t.Optional[str]


def encode_message_cookie(message: list[MessageFlash]) -> bytes:
    data = b64encode(json.dumps(g.next_flash_messages).encode("utf-8"))
    cookie = itsdangerous.TimestampSigner(str(Config.SECRET_KEY)).sign(data)
    return cookie


def flash_message(message: str, category: t.Optional[str] = None):
    if not g.next_flash_messages:
        g.next_flash_messages = []
    message_flash = MessageFlash(message=message, category=category)
    g.next_flash_messages.append(message_flash)  # type:ignore


def get_flashed_messages() -> t.Optional[list[MessageFlash]]:
    return g.flash_messages
