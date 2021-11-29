import json

from pydantic import BaseModel, ValidationError
from pydantic.error_wrappers import ErrorWrapper


class APIError(Exception):
    @classmethod
    def to_dict(cls):
        errors = ErrorWrapper(cls(), "Register")
        return json.loads(ValidationError([errors], BaseModel).json())


class WrongHashKey(APIError):
    pass


class WrongPassword(APIError):
    pass


def validate(body: BaseModel, *args, msg: str = "Need this value") -> dict | None:
    _body = body.dict()

    return validate_dict(_body)


def validate_dict(_dict: dict, *args, msg: str = "Need this value") -> dict | None:
    errors = []

    for field in args:
        if not _dict[field]:
            errors.append(ErrorWrapper(ValueError(msg), field))

    if len(errors):
        return json.loads(ValidationError(errors, BaseModel).json())


def error_to_dict(*errors: Exception):
    errors = list(map(lambda error: ErrorWrapper(error, "Register"), errors))
    return json.loads(ValidationError(errors, BaseModel).json())
