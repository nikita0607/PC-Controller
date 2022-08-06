"""
Enter dot to api_server
"""

from typing import Dict

from fastapi import FastAPI

import methods

from computers import ComputerController

from api_errors import null_missed_dict, validate_dict, Error
from api_errors import WrongHashKey, WrongLoginData

from connection import Connection
from database import Database

from debug import d_print


class Body:
    """
    Body of client response
    """

    method: str
    username: str
    password: str

    hash_key: str
    c_hash_key: str = None

    def __init__(self, body: dict):
        self._dict = body.copy()
        body = null_missed_dict(body, "password", "hash_key")
        for i in body:
            setattr(self, i, body[i])

    def __contains__(self, item):
        return hasattr(self, item)

    def dict(self):
        """
        Translate request-object to raw dict
        """
        return self._dict.copy()


app = FastAPI()
db = Database()

hash_cash: Dict[str, str] = {}


@app.get("/api-doc")
def api_doc():
    """
    Documenration page
    """

    return "Welcome to the doc!"


@app.post("/api")
async def api(body: dict):
    """
    Processing user's api request

    This function check some fields, setup connection-info and call
    method-parser function.
    """

    d_print(body)
    _error = validate_dict(body, "method", "username")
    if _error:
        return _error.json_alone()
    body = Body(body)

    connection = Connection(body.username, False, 0)

    if body.username:
        if await db.check_user_login(connection.login):
            connection.registered_user = True

    if "name" in body:
        if body.c_hash_key:
            _error = await comp_check_computer_hash_key(
                body.username, body.name, body.c_hash_key
            )
            if not Error.is_error(_error):
                connection.access_level = 1
            else:
                return WrongHashKey.json_alone()

    if body.password:
        if await db.check_user(body.username, body.password):
            connection.access_level = 2
        else:
            return WrongLoginData.json_alone()

    res = await methods.MethodParser.parse_action(connection, body.dict())
    d_print("DEBUG RES:", res)
    return res
