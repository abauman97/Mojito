from mojito import auth
from asyncio import sleep


class PasswordAuth(auth.AuthBase):
    async def authorize(self, scopes: list[str]) -> bool:
        await sleep(0.5)
        return True

    async def authenticate(self, request: auth.Request, username: str, password: str):
        await sleep(0.5)
        return (True, ["admin"])
