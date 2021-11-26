import json

from fastapi import FastAPI

from pydantic import BaseModel

from config import *

from api_errors import *
from computer import *


class Body(BaseModel):
    action: str
    username: str

    password: str = None
    hash_key: str = None


app = FastAPI()
comp_handler = ComputerHandler()
db = Database()

hash_cash: dict[str] = {}


@app.get("/api-doc")
def api_doc():
    return "Welcome to the doc!"


@app.post("/api")
async def api(body: Body):
    pass_auth = True

    if body.action == "register":
        error = validate(body, "password")
        if error:
            return error

        res = await db.new_user(body.username, body.password)
        return {"result": res}

    if body.hash_key:
        pass_auth = False
        if not await db.check_hash_key(body.username, body.hash_key):
            return error_to_dict(WrongHashKey())
    elif body.password:
        if not await db.check_user(body.username, body.password):
            return WrongPassword.to_dict()
    else:
        return validate(body, "password", "hash_key")

