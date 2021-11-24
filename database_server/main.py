import json

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from pydantic import BaseModel, ValidationError
from pydantic.error_wrappers import ErrorWrapper

from database import Database


class Body(BaseModel):
    action: str

    login: str = None
    password: str = None


app = FastAPI()
db = Database()


@app.post("/")
async def response(body: Body):

    if body.action == "is_user":
        if not body.login:
            return json.loads(ValidationError([ErrorWrapper(ValueError(), "login")], Body).json(indent=0))
        return {"result": db.is_user(body.login)}

    if body.action == "new_user":
        if not body.login:
            pass


    return {"Your name": body.login}