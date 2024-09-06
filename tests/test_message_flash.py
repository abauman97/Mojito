from mojito import AppRouter, JSONResponse, Mojito, flash_message, get_flashed_messages
from mojito.testclient import TestClient

app = Mojito()
router = AppRouter()

client = TestClient(app)


@router.route("/set-flash")
def set_flash():
    flash_message("flash_set")
    flash_message("flash message 2", "warn")


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
    assert "flash_set" == messages[0].get("message")
    assert "flash message 2" == messages[1].get("message")
    assert "warn" == messages[1].get("category")
