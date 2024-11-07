from mojito import Mojito, Request, templating
from mojito.testclient import TestClient

app = Mojito()
client = TestClient(app)
import os

templates = templating.Templates(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
)


@app.route("/")
def index_route(request: Request):
    return templates.TemplateResponse(request, "number.jinja", {"number": 1})


@app.route("/number_2")
def number_two_route(request: Request):
    return templates.TemplateResponse(
        request, "number.jinja", {"number": 2}, block="content"
    )


def test_index_template():
    result = client.get("/")
    assert result.is_success
    assert "<h1>Here's the header!</h1>" in result.text
    assert "<p>The number is: 1</p>" in result.text


def test_template_partials():
    result = client.get("/number_2")
    assert result.is_success
    assert "<p>The number is: 2</p>" in result.text
    assert "<h1>Here's the header!</h1>" not in result.text
