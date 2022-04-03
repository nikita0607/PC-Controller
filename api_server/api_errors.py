import json

from typing import Union

from pydantic import BaseModel, ValidationError
from pydantic.error_wrappers import ErrorWrapper


class Error:
    @classmethod
    def is_error(cls, other):
        if hasattr(other, "is_error"):
            return True
        return False


class APIError(Exception):
    msg = "Unknown error"
    type = "unknown_error"
    code = 0
    is_error = True

    def __new__(cls, loc="", _init_this=False):
        if _init_this:
            return super().__new__(cls, cls.msg)
        return APIErrorInit(cls.msg, cls.code, loc, cls.type)

    @classmethod
    def json(cls, loc: str = ""):
        _error = {"loc": loc, "msg": cls.msg,  "type": cls.type, "code": cls.code}

        return _error

    @classmethod
    def json_alone(cls, loc: str = ""):
        return {"result": "error", "errors": [cls.json()]}


class APIErrorInit(Exception):
    def __init__(self, msg: str = "Unknown error", code: int = 0, loc: str = "", _type: str = "unknown_error"):
        self.msg = msg
        self.type = _type
        self.loc = loc
        self.code = code
        self.is_error = True

    def json(self):
        _error = {"loc": self.loc,  "msg": self.msg, "type": self.type, "code": self.code}

        return _error

    def json_alone(self):
        return {"result": "error", "errors": [self.json()]}


class APIErrorList:
    def __init__(self, *errors):
        self.errors: list[APIErrorInit] = list(errors)
        self.is_error = True

    @property
    def count(self):
        return len(self.errors)

    def add(self, error: APIErrorInit):
        self.errors.append(error)

    def json(self) -> list:
        errors: list[dict] = [error.json() for error in self.errors]
        return errors

    def json_alone(self) -> dict:
        return {"result": "error", "errors": self.json()}

    def __str__(self):
        return str(self.errors)


class MethodNotFound(APIError):
    msg = "Method not found"
    code = 6
    type = "method_not_found"


class MissedValue(APIError):
    msg = "Missed required value"
    code = 5
    type = "missed_value"


class WrongHashKey(APIError):
    msg = "Wrong hash key"
    code = 1
    type = "wrong_hash_key"


class WrongLoginData(APIError):
    msg = "Wrong login or password"
    code = 2
    type = "wrong_login_data"


class UnknownComputer(APIError):
    msg = "Unknown computer"
    code = 3
    type = "unknown_computer"


class NotEnoughtAccessLevel(APIError):
    msg = "Not enought access level"
    code = 7
    type = "not_enought_access_level"


class NameBusy(APIError):
    msg = "Name busy"
    code = 4
    type = "name_busy"


def validate(body: BaseModel, *args, msg: str = "Need this value") -> Union[APIErrorList, None]:
    _body = body.dict()

    return validate_dict(_body)


def validate_dict(_dict: dict, *args, msg: str = "Need this value") -> Union[APIErrorList, None]:
    error_list = APIErrorList()

    for field in args:
        if field not in _dict or not _dict[field]:
            error_list.add(MissedValue(field))

    if error_list.count:
        return error_list

    return None


def null_missed_dict(_dict: dict, *args):
    for i in args:
        if i not in _dict:
            _dict[i] = None
    return _dict


def error_to_dict(*errors: Exception):
    errors = list(map(lambda error: ErrorWrapper(error, "Register"), errors))
    return json.loads(ValidationError(errors, BaseModel).json())
