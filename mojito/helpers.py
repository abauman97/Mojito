import json
from base64 import b64decode, b64encode

import itsdangerous
from .globals import g
from .config import Config


def encode_message_cookie(message: list[str]) -> bytes:
    data = b64encode(json.dumps(g.next_flash_messages).encode("utf-8"))
    cookie = itsdangerous.TimestampSigner(str(Config.SECRET_KEY)).sign(data)
    return cookie


def decode_message_cookie(cookie: str) -> list[str]:
    data = itsdangerous.TimestampSigner(str(Config.SECRET_KEY)).unsign(cookie)
    return json.loads(b64decode(data))


def flash_message(message: str):
    if not g.next_flash_messages:
        g.next_flash_messages = []
    g.next_flash_messages.append(message)  # type:ignore


def get_flashed_messages() -> list[str] | None:
    return g.flash_messages
