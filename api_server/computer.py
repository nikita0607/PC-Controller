import asyncio
from api_server.api_errors import APIError, NameBusy, UnknownComputer, WrongHashKey

from connection import Connection
from api_errors import *

from hashlib import sha256
from random import randint


class Method:
    def __init__(self, string, *required_values, need_hash_key: bool = True):
        self.string = string
        self.required_values = required_values

        if need_hash_key:
            required_values.append("hash_key")

    def __str__(self):
        return self.string

    def __eq__(self, other):
        return str(self) == other

    def validate(self, _dict: dict) -> dict | None:
        res = validate_dict(_dict, *self.required_values)
        return res if res else self


class Methods:
    CONNECT = Method("computer.connect", "name", need_hash_key=False)

    @classmethod
    def find_and_validate(cls, _dict) -> dict | Method | None:
        methods: list[Method] = [cls.__dict__[i] for i in cls.__dict__ if isinstance(cls.__dict__[i], Method)]

        for method in methods:
            if method.string == _dict["method"]:
                return method.validate(_dict)


class Computer:
    def __init__(self, username: str, name: str, hash_key: str):
        self.username = username
        self.name = name
        self.hash_key = hash_key


class ComputerController:
    def __init__(self):
        self.computers: dict[str, dict[str, Computer]] = {}

    def get_computer_by_name(self, username: str, name: str) -> Computer | APIError:
        if username in self.computers and name in self.computers[username]:
            return self.computers[username][name]
        return UnknownComputer

    def check_computer_hash_key(self, username: str, name: str, hash_key: str) -> APIError | None:
        _comp = self.get_computer_by_name(username, name)

        if isinstance(_comp, APIError):
            return _comp
        
        if hash_key != _comp.hash_key:
            return WrongHashKey

    def parse_action(self, conn: Connection, action: dict):
        error = validate_dict(action, "method")

        if error:
            return error

        _method = action["method"]
        validate_result = Methods.find_and_validate(action)

        if validate_result is None:
            pass

        if isinstance(validate_result, dict):
            return validate_result

        method = validate_result

        name_error = validate_dict(action, "name")
        hash_key_error = (validate_dict(action, "name", "hash_key") or
                            self.check_computer_hash_key(action["username"], action["name"], action["hash_key"]))
        
        if method == Methods.CONNECT:
            if name_error:
                return name_error.to_dict()
            if not self.get_computer_by_name(action["username"], action["name"]):
                return NameBusy.to_dict()
            new_hash_key = sha256((action["username"]+action["name"]+str(randint(0, 100))).encode()).hexdigest()

            print(f"New hash key: {new_hash_key}")

            computer = Computer(action["username"], action["name"], new_hash_key)

            return {"result": True}


if __name__ == '__main__':  
    print(Methods.find_and_validate({"method": "connect"}))