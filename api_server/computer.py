import asyncio

from connection import Connection
from api_errors import *


class Method:
    def __init__(self, string, *required_values):
        self.string = string
        self.required_values = required_values

    def __str__(self):
        return self.string

    def __eq__(self, other):
        return str(self) == other

    def validate(self, _dict: dict) -> dict | None:
        return validate_dict(_dict, *self.required_values)


class Methods():
    CONNECT = Method("connect", "name")

    @classmethod
    def find_and_validate(cls, _dict):
        methods: list[Method] = [cls.__dict__[i] for i in cls.__dict__ if isinstance(cls.__dict__[i], Method)]

        for method in methods:
            pass


class Computer:
    def __init__(self, username: str):
        self.username = username


class ComputerController:
    def __init__(self):
        self.computers: dict[str, dict[str, Computer]] = {}

    def parse_action(self, conn: Connection, action: dict):
        error = validate_dict(action, "method")

        if error:
            return error

        method = action["method"]


if __name__ == '__main__':
    print(Methods.find_and_validate("connect"))