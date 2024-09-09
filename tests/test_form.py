import os

import pytest
from pydantic import (
    BaseModel,
    Field,
    ValidationError,
)

from mojito import JSONResponse, Mojito, Request, Response
from mojito.forms import Form, FormManager, UploadFile
from mojito.testclient import TestClient

app = Mojito()
client = TestClient(app)


class FormTest(BaseModel):
    field_1: str
    field_2: str
    field_3: int = Field(default=10)  # Optional field


@app.route("/", methods=["POST"])
async def process_form(request: Request):
    try:
        form = await Form(request, FormTest)
        return JSONResponse(form.model_dump())
    except ValidationError as e:
        return Response(e.__str__(), status_code=500)


@pytest.mark.parametrize(
    ("form_data", "status"),
    [
        (
            {
                "field_1": "field one",
                "field_2": "field two",
                "field_3": 15,
            },
            200,
        ),
        (
            {
                "field_1": "field one",
                "field_2": "field two",
                "field_3": "nope",  # Invalid type
            },
            500,
        ),
        ({"field_1": "field one", "field_2": "field two"}, 200),
        (
            {
                "field_1": "field one",
                "field_2": "field two",
                "extra_field": "extra field",  # Ignored field
            },
            200,
        ),
        (
            {
                "field_1": "field one",  # Missing field_2
            },
            500,
        ),
    ],
)
def test_form_processing(form_data: dict[str, str], status: int):
    result = client.post("/", data=form_data)
    assert result.status_code == status
    if result.status_code == 200:
        assert result.json().get("field_1") == form_data.get("field_1")


class FormWithFileTest(BaseModel):
    field_1: str = ""
    file_1: UploadFile


@app.route("/upload_file", methods=["POST"])
async def process_upload_file_form(request: Request):
    async with FormManager(request, FormWithFileTest) as form:
        file_content = await form.file_1.read()
        return file_content.decode()


def test_form_file_processing():
    directory = os.path.dirname(__file__)
    file = open(directory + "/txt_file.txt", "rb")
    file_content = file.read()
    result = client.post("/upload_file", files={"file_1": file})
    assert result.status_code == 200
    assert result.text == file_content.decode()
