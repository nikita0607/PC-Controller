import json

from fastapi import FastAPI

from pydantic import BaseModel

from config import *

from api_errors import *
from computer import *
from connection import Connection
from database import Database


class Body(BaseModel):
    method: str
    username: str
    name: str = None

    password: str = None
    hash_key: str = None
    computer_hash_key: str = None


app = FastAPI()
comp_controller = ComputerController()
db = Database()

hash_cash: dict[str] = {}


@app.get("/api-doc")
def api_doc():
    return "Welcome to the doc!"


@app.post("/api")
async def api(body: Body):
    connection = Connection(body.username, False)

    if body.username:
        if db.check_user_login(connection.login):
            connection.is_user = True

    if body.hash_key:
        pass_auth = False
        if not await db.check_hash_key(body.username, body.hash_key):
            return WrongHashKey.to_dict()
        connection.logged_in = True
        connection.logged_with_password = False
    elif body.password:
        if not await db.check_user(body.username, body.password):
            return WrongLoginData.to_dict()
        connection.logged_in = True
        connection.logged_with_password = True

    if body.computer_hash_key:
        connection.computer_hash_key = body.computer_hash_key
    
    return comp_controller.parse_action(connection, body.dict())


