import json

from fastapi import FastAPI

from pydantic import BaseModel, ValidationError
from pydantic.error_wrappers import ErrorWrapper

from database import Database


class AlreadyRegister(Exception):
    def __init__(self, msg: str = ""):
        super().__init__(msg)


class Body(BaseModel):
    action: str

    login: str = None
    password: str = None
    hash_key: str = None


app = FastAPI()
db = Database()


def validate(body: BaseModel, *args) -> dict | None:
    _body = body.dict()
    errors = []

    for field in args:
        if not _body[field]:
            errors.append(ErrorWrapper(ValueError(f"Heey, send me {field}"), field))

    if len(errors):
        return json.loads(ValidationError(errors, Body).json())


def error_to_dict(*errors: Exception):
    errors = list(map(lambda error: ErrorWrapper(error, "Register"), errors))
    return json.loads(ValidationError(errors, Body).json())


@app.get("/test")
def test():
    return "Test"


@app.post("/")
async def response(body: Body):

    if body.action == "check_user_login":
        error = validate(body, "login")
        if error:
            return error
        return {"result": db.check_user_login(body.login)}

    if body.action == "login":
        error = validate(body, "login", "password")
        if error:
            return error
        return {"result": db.check_user(body.login, body.password)}

    if body.action == "register":
        error = validate(body, "login", "password")
        if error:
            return error

        if not db.new_user(body.login, body.password):
            return error_to_dict(AlreadyRegister())
        return {"result": "Ok"}

    if body.action == "check_hash_key":
        error = validate(body, "login", "hash_key")
        if error:
            return error

        return {"result": db.check_hash_key(body.login, body.login)}

    if body.action == "check_user":
        error = validate(body, "login", "password")
        if error:
            return error

        return {"result": db.check_user(body.login, body.password)}
