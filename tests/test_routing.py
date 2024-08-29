import pytest

from mojito.testclient import TestClient

from .main import app

client = TestClient(app)


@pytest.mark.parametrize(
    "path,status,expected_response",
    [
        ("/", 200, "index_response"),
        ("/doesnt_exist", 404, "Not Found"),
        ("/async_route", 200, "async_route_response"),
    ],
)
def test_get_index(path: str, status: int, expected_response: str):
    response = client.get(path)
    assert response.status_code == status
    assert response.text == expected_response


@pytest.mark.parametrize(
    "path_param,query_param_1,status", [(1, "param", 200), ("nope", "param", 404)]
)
def test_params(path_param: int, query_param_1: str, status: int):
    response = client.get(f"/{path_param}?query_param_1={query_param_1}")
    assert response.status_code == status
    if response.status_code == 200:
        assert response.json() == {"id": path_param, "query_param_1": query_param_1}


def test_application_route():
    response = client.get("/app-route")
    assert response.status_code == 200
    assert response.text == "app-route"
