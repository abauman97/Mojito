from contextlib import asynccontextmanager
from typing import Any, TypeVar

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema
from starlette.datastructures import UploadFile as StarletteUploadFile

from .requests import Request

try:
    from pydantic import BaseModel
except ModuleNotFoundError:
    raise ModuleNotFoundError(
        "Form requires pydantic being installed. \npip install pydantic"
    )


PydanticModel = TypeVar("PydanticModel", bound=BaseModel)


@asynccontextmanager
async def FormManager(
    request: Request,
    model: type[PydanticModel],
    max_files: int = 1000,
    max_fields: int = 1000,
):
    """Read form data from the request and validate it's content against a Pydantic model
    and return the valid Pydantic model. Extra data in the form is ignored and not passed into the
    Pydantic model. This does not work for processing files. You must use the request directly to get and read
    from files before using this function to read and validate the other form fields. See
    https://www.starlette.io/requests/#request-files for working with files.

    Args:
        request (Request): Mojito Request object
        model (PydanticModel): The Pydantic model to validate against
        max_files (int): The maximum number of files for Starlette to allow
        max_fields (int): The maximum number of fields for Starlette to allow

    Yields:
        PydanticModel: The validated Pydantic model


    Raises:
        ValidationError: Pydantic validation error
    """
    async with request.form(max_files=max_files, max_fields=max_fields) as form:
        valid_model = model.model_validate(dict(form.items()))
        yield valid_model  # Yield result while in context of request.form()


async def Form(
    request: Request,
    model: type[PydanticModel],
    max_files: int = 1000,
    max_fields: int = 1000,
):
    "Validates the form fields against the model"
    async with request.form(max_files=max_files, max_fields=max_fields) as form:
        valid_model = model.model_validate(dict(form.items()))
        return valid_model


class UploadFile(StarletteUploadFile):
    """An uploaded file included as part of the request data.

    This is a subclass of starlette.datastructures.UploadFile that can be used in a Pydantic
    BaseModel class. Pydantic will pass the model through as-is without validation.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        # Allow this file type to pass through pydantic without schema validation
        return core_schema.any_schema()
