import json
import os
import methods
import controller

from fastapi import FastAPI

from pydantic import BaseModel
from typing import Dict

from config import *

from api_errors import *
from connection import Connection
from database import Database


class Body:
    method: str
    username: str
    password: str

    hash_key: str
    computer_hash_key: str

    def __init__(self, body: dict):
        self._dict = body.copy()
        body = null_missed_dict(body, "password", "hash_key")
        for i in body:
            setattr(self, i, body[i])

    def dict(self):
        return self._dict.copy()


app = FastAPI()
comp_controller = controller.ComputerController()
db = Database()

hash_cash: Dict[str, str] = {}


@app.get("/api-doc")
def api_doc():
    return "Welcome to the doc!"


@app.post("/api")
async def api(body: dict):
    _error = validate_dict(body, "method", "username")
    if _error:
        print(_error)
        return _error.json_alone()
    body = Body(body)

    connection = Connection(body.username, False)

    if body.username:
        if await db.check_user_login(connection.login):
            connection.is_user = True

    if body.password:
        if not await db.check_user(body.username, body.password):
            connection.logged_in = True
            connection.logged_with_password = True
    elif body.hash_key:
        pass_auth = False
        if await db.check_hash_key(body.username, body.hash_key):
            connection.logged_in = True
            connection.logged_with_password = False
    
    res = await methods.MethodParser.parse_action(comp_controller, connection, body.dict())
    print(res)
    return res
