import json

from pydantic import BaseModel, ValidationError
from pydantic.error_wrappers import ErrorWrapper


class APIError(Exception):
    msg = "Unknown error"
    code = 0

    @classmethod
    def to_dict(cls):
        error = ErrorWrapper(cls(cls.msg))
        return json.loads(ValidationError([error], BaseModel).json())


class APIErrorList:
    def __init__(self, *errors):
        self.errors: list[APIError] = errors

    @property
    def count(self):
        return len(self.errors)

    def add(self, error: APIError):
        self.errors.append(error)

    def to_dict(self):
        errors: list[ErrorWrapper] = list(map(lambda error: ErrorWrapper(error), self.errors))
        return json.loads(ValidationError(errors, BaseModel).json())


class WrongHashKey(APIError):
    msg = "Wrong hash key"
    code = 1


class WrongLoginData(APIError):
    msg = "Wrong login or password"
    code = 2


class UnknownComputer(APIError):
    msg = "Unknown computer"
    code = 3


class NameBusy(APIError):
    msg = "Name busy"
    code = 4


def validate(body: BaseModel, *args, msg: str = "Need this value") -> APIErrorList | None:
    _body = body.dict()

    return validate_dict(_body)


def validate_dict(_dict: dict, *args, msg: str = "Need this value") -> APIErrorList | None:
    error_list = APIErrorList()

    for field in args:
        if not _dict[field]:
            error_list.add(ValueError(msg))

    if error_list.count:
        return error_list

    return None


def error_to_dict(*errors: Exception):
    errors = list(map(lambda error: ErrorWrapper(error, "Register"), errors))
    return json.loads(ValidationError(errors, BaseModel).json())
