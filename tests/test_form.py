from mojito import Mojito, Request, Form, Response
from mojito.testclient import TestClient
from pydantic import BaseModel, ValidationError, Field
import pytest

app = Mojito()
client = TestClient(app)

class FormTest(BaseModel):
    field_1: str
    field_2: str
    field_3: int = Field(default=10) # Optional field

@app.route("/", methods=["GET", "POST"])
async def process_form(request: Request):
    if request.method == "POST":
        try:
            await Form(request, FormTest)
        except ValidationError as e:
            return Response(e.__str__(), status_code=500)
        

@pytest.mark.parametrize(("form_data","status"), [
        ({
        "field_1": "field one",
        "field_2": "field two",
        "field_3": 15,
    },200),
            ({
        "field_1": "field one",
        "field_2": "field two",
        "field_3": "nope", # Invalid type
    },500),
    ({
        "field_1": "field one",
        "field_2": "field two"
    },200),
    ({
        "field_1": "field one",
        "field_2": "field two",
        "extra_field": "extra field" # Ignored field
    },200), 
    ({
        "field_1": "field one", # Missing field_2
    },500)
])
def test_form_processing(form_data: dict[str, str], status: int):
    result = client.post('/', data=form_data)
    assert result.status_code == status