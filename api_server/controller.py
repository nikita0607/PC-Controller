import asyncio

from connection import Connection
from computer import Computer, Connection

from api_errors import Error,  APIError, APIErrorList, NameBusy, UnknownComputer, MethodNotFound
from api_errors import WrongHashKey, WrongLoginData, validate_dict, APIErrorInit

from database import Database

from hashlib import sha256
from random import randint

from typing import Dict, Union, Type


class ComputerController:
    this = None

    def __new__(cls, *args, **kwargs):
        if not cls.this:
            cls.this = super().__new__(cls)
        return cls.this

    def __init__(self):
        self.computers: Dict[str, Dict[str, Computer]] = {}
        self.db = Database()

    async def get_computer_by_name(self, username: str, name: str) -> Computer | Type[UnknownComputer]:
        if username in self.computers and name in self.computers[username]:
            return self.computers[username][name]
        return UnknownComputer

    async def get_computer_with_hashkey(self, username: str, name: str, c_hash_key: str) -> Union[Computer, APIError]:
        _computer = await self.get_computer_by_name(username, name)
        return _computer if _computer.hash_key == c_hash_key else WrongHashKey

    async def disconnect_computer(self, username, name):
        del self.computers[username][name]

    async def check_computer_hash_key(self, username: str, name: str, hash_key: str) -> Union[APIError, None]:
        _comp = await self.get_computer_by_name(username, name)

        if Error.is_error(_comp):
            return _comp

        if hash_key != _comp.hash_key:
            return WrongHashKey

    async def check_computer(self, username: str, name: str) -> Union[APIError, None]:
        _comp = await self.get_computer_by_name(username, name)
        if Error.is_error(_comp):
            return _comp
