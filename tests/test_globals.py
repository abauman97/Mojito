import asyncio

import httpx

from mojito import Mojito, Request, g

app = Mojito()


@app.route("/{g_message}")
async def get_and_set_g(request: Request, g_message: int):
    g.test_message = g_message
    await asyncio.sleep(1)
    assert g.test_message == g_message


async def get_g(i: int):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get(f"/{i}")


async def main():
    await asyncio.gather(*[get_g(i) for i in range(1000, 2000)])


def test_g_isolation():
    asyncio.run(main())
    assert True


if __name__ == "__main__":
    asyncio.run(main())
