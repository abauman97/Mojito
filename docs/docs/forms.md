# Forms
Mojito provides a simple interface for validating form inputs against Pydantic models for CRUD application.

## Using form processing
The `Form` and `FormManager` functions provide a layer on top of Starlettes `request.form()`. That layer on top helps to clean up normal headaches associated with form entries. To describe it, let's start with an example.

# Basic form procsesing
First define your form inputs as a Pydantic model and validate the form data against it using the `Form` function.
```py
from pydantic import BaseModel
from mojito import Mojito, Request, forms

app = Mojito()

class UserCreateForm(BaseModel):
    name: str
    email: str
    permissions: list[str]

@app.route('/create_user', methods=["GET", "POST"])
async def create_user(request: Request):
    if request.method == "POST":
        form = await forms.Form(request, UserCreateForm)
        print(form.model_dump())
    return """
    <form method="post">
        <div>
            <label for="name">Name</label>
            <input name="name" id="name" type="text">
        </div>
        <div>
            <label for="name">Name</label>
            <input name="name" id="name" type="text">
        </div>
        <div id="permissions">
            <div>
                <label for="readPermission">Read</label>
                <input type="checkbox" name="permissions" value="read" id="readPermission">
            </div>
            <div>
                <label for="writePermission">Write</label>
                <input type="checkbox" name="permissions" value="write" id="writePermission">
            </div>
        </div>
        <button type="submit">Submit</button>
    </form>
    """
```

When this form is submitted the `Form` function will first preprocess the form data to combine fields with the same name, like the checkboxes above, into a list and remove fields submitted as empty strings before sending them to be validated by Pydantic. 

## Forms with files
The `FormManager` is an asynccontextmanager providing the same functionality as form except it can be used within a context manager to maintain the open form data, alllowing for reading and working with uploaded files. This can also be used when you want to keep working with Starlettes `request.form()` data directly after data validation.

The `form` module provides `UploadFile` as a Pydantic compatible alternaitive to Starlettes `UploadFile` to type files in your Pydantic models.
