from mojito import AppRouter, JSONResponse, Mojito, flash_message, get_flashed_messages
from mojito.testclient import TestClient

app = Mojito()
router = AppRouter()

client = TestClient(app)


@router.route("/set-flash")
def set_flash():
    flash_message("flash_set")
    flash_message("flash message 2")


@router.route("/get-flash")
def get_flash():
    return JSONResponse(get_flashed_messages())


app.include_router(router)


def test_message_flash():
    response = client.get("/set-flash")
    assert response.status_code == 200
    response = client.get("/get-flash")
    assert response.status_code == 200
    messages = response.json()
    assert "flash_set" in messages
    assert "flash message 2" in messages
