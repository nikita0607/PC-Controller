import json

from pydantic import BaseModel, ValidationError
from pydantic.error_wrappers import ErrorWrapper


class APIError(Exception):
    msg = "Unknown error"
    code = 0

    def __init__(self, loc=""):
        super().__init__(self.msg)
        self._loc = loc

    def to_wrapper(self):
        return ErrorWrapper(self, self._loc)

    def to_dict(self):
        error = self.to_wrapper()

        _json: dict = json.loads(ValidationError([error], BaseModel).json())[0]
        _json.pop("ctx")

        return _json

    @classmethod
    def to_dict(self):
        error = ErrorWrapper(cls(cls.msg), "")

        _json: dict = json.loads(ValidationError([error], BaseModel).json())[0]
        _json.pop("ctx")

        return _json


class APIErrorList:
    def __init__(self, *errors):
        self.errors: list[APIError] = list(errors)

    @property
    def count(self):
        return len(self.errors)

    def add(self, error: APIError):
        self.errors.append(error)

    def to_dict(self):
        errors: list[ErrorWrapper] = [error.to_wrapper() for error in self.errors]
        _json: list = json.loads(ValidationError(errors, BaseModel).json())

        for i in range(len(_json)):
            _json[i].pop("ctx")
        
        return _json

    def __str__(self):
        return str(self.errors)


class MissedValue(APIError):
    msg = "Missed required value"
    code = 5


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
        if field not in _dict or not _dict[field]:
            error_list.add(MissedValue(field))

    if error_list.count:
        return error_list

    return None


def error_to_dict(*errors: Exception):
    errors = list(map(lambda error: ErrorWrapper(error, "Register"), errors))
    return json.loads(ValidationError(errors, BaseModel).json())
