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

from debug import d_print


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

    def __contains__(self, item):
        return True if (self, item) else False

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
        return _error.json_alone()
    body = Body(body)

    connection = Connection(body.username, False, 0)

    if body.username:
        if await db.check_user_login(connection.login):
            connection.registered_user = True

    if "name" in body:
        _error = await comp_controller.check_computer_hash_key(body.username, body.name, body.computer_hash_key)
        if Error.is_error(_error):
            return _error.json_alone()
        connection.access_level = 1

    if body.password:
        if await db.check_user(body.username, body.password):
            connection.access_level = 2
    elif body.hash_key:
        if await db.check_hash_key(body.username, body.hash_key):
            connection.access_level = 2

    res = await methods.MethodParser.parse_action(comp_controller, connection, body.dict())
    d_print("DEBUG RES:", res)
    return res
