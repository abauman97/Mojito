from typing import TypeVar
from .requests import Request

try:
    from pydantic import BaseModel
except ModuleNotFoundError:
    raise ModuleNotFoundError("Form requires pydantic being installed. \npip install pydantic")


PydanticModel = TypeVar('PydanticModel', bound=type[BaseModel])
async def Form(request: Request, model: PydanticModel) -> PydanticModel:
    """Read form data from the request and validate it's content against a Pydantic model 
    and return the valid Pydantic model. Extra data in the form is ignored and not passed into the
    Pydantic model.

    Args:
        request (Request): Mojito Request object
        model (PydanticModel): The Pydantic model to validate against

    Returns:
        PydanticModel: The validated Pydantic model

    Raises:
        ValidationError: Pydantic validation error
    """
    async with request.form() as form:
        valid_model = model.model_validate(dict(form.items()))
    return valid_model