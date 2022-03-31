import computer

import connection
from debug import d_print

from controller import ComputerController

from typing import Union, List
from enum import Enum

from api_errors import Error, APIError, APIErrorList, NameBusy, UnknownComputer, MethodNotFound
from api_errors import WrongHashKey, WrongLoginData, validate_dict, APIErrorInit
from api_errors import NotEnoughtAccessLevel

from database import Database

from hashlib import sha256
from random import randint


class MethodSupport:
    @staticmethod
    def get_database(callback):
        async def wrapper(controller, conn, action, *args,
                          **kwargs):
            return await callback(controller, conn, action, *args, **kwargs,
                                  database=Database())

        return wrapper

    @staticmethod
    def get_computer(raise_not_found: bool = True):
        """ Decorator return computer with recieved 'username' and 'name' """

        def dec(callback):
            async def wrapper(controller, conn, action, *args, **kwargs):

                if "for_name" in action:

                    _computer = await controller.get_computer_by_name(
                        action["username"],
                        action["for_name"])

                else:
                    _computer = await controller.get_computer_with_hashkey(
                        action["username"],
                        action["name"],
                        action["c_hash_key"])


                if Error.is_error(_computer) and raise_not_found:
                    return _computer.json_alone()

                return await callback(controller, conn, action, *args,
                                      **kwargs, _computer=_computer)

            return wrapper

        return dec


class Method:
    methods_callbacks = {}

    def __init__(self, string, *required_values, access_level: int = 1):
        self.string = string
        self.required_values = list(required_values)
        self.access_level = access_level

    def __str__(self):
        return self.string

    def __eq__(self, other):
        return str(self) == other

    def validate(self, _dict: dict) -> APIErrorList:
        res = validate_dict(_dict, *self.required_values)
        return res if res else self

    @classmethod
    def method_callback(cls, method: str):
        def wrapper(callback):
            cls.methods_callbacks[method] = callback
            return callback

        return wrapper

    async def call_method(self, controller, conn, action: dict):
        return await self._call_method(self.string, controller, conn, action)

    @classmethod
    async def _call_method(cls, method: str, controller, conn, action):
        if isinstance(method, Method):
            method = method.string
        return await cls.methods_callbacks[method](controller, conn, action)


@Method.method_callback("computer.connect")
@MethodSupport.get_computer(False)
async def computer_connect(controller, conn, action: dict, _computer):
    print("connect")
    if not conn.registered_user:
        return WrongLoginData.json_alone("username")

    if not Error.is_error(_computer):
        return NameBusy.json_alone("name")

    new_hash_key = sha256((action["username"] + action["name"] + str(randint(0, 100))).encode()).hexdigest()

    print(f"New hash key: {new_hash_key}")

    _computer = computer.Computer(conn.login, action["name"], new_hash_key)

    if conn.login not in controller.computers:
        controller.computers[conn.login] = {}

    controller.computers[_computer.username][_computer.name] = _computer

    return {"result": True, "hash_key": new_hash_key}


@Method.method_callback("computer.ping")
async def ping(*args, **kwargs):
    return {"result": True}


@Method.method_callback("computer.ping_error")
async def ping_error(*args, **kwargs):
    return APIError.json_alone()


@Method.method_callback("computer.button.add")
@MethodSupport.get_computer()
async def computer_add_button(controller: ComputerController, conn, action,
                              _computer: computer.Computer):
    _computer.add_button(action["button_name"], action["button_text"])
    return {"result": True}


@Method.method_callback("computer.button.click")
@MethodSupport.get_computer()
async def computer_add_button(controller, conn, action, _computer: computer.Computer):
    _computer.button_click(action["button_name"])
    return {"result": True}


@Method.method_callback("user.register")
@MethodSupport.get_database
async def user_register(controller, conn, action, database: Database):
    if conn.is_user:
        return NameBusy.json_alone()

    await database.new_user(conn.login, action["password"])
    return {"result": True}


@Method.method_callback("user.get_computers")
async def user_get_computers(controller: ComputerController, conn, action):
    if action["username"] not in controller.computers:
        return {"result": []}

    return {"result": [comp.json()
                       for _, comp in controller.computers[action["username"]].items()]}


@Method.method_callback("computer.get_info")
@MethodSupport.get_computer()
async def computer_info(controller, conn, action, _computer: computer.Computer):
    return {"result": _computer.json()}


@Method.method_callback("computer.get_events")
@MethodSupport.get_computer()
async def get_events(controller, conn, action, _computer: computer.Computer):
    _id = action["start_id"] if "start_id" in action else 0
    return {"result": _computer.json_events(start_id=_id)}


@Method.method_callback("computer.disconnect")
@MethodSupport.get_computer()
async def disconnect(controller: ComputerController, conn,
                     action, _computer: computer.Computer):
    await controller.disconnect_computer(_computer.username, _computer.name)
    return {"result": True}


class MethodParser:
    @staticmethod
    async def parse_action(_controller: ComputerController,
                           conn: connection.Connection, action: dict):
        error = validate_dict(action, "method")

        if error:
            print("Error: ", error)
            return error

        _method = action["method"]

        validate_result = await Methods.or_validate(action, Methods, UserMethods)

        if validate_result is None:
            return MethodNotFound.json_alone()

        if Error.is_error(validate_result):
            return validate_result.json_alone()

        method: Method = validate_result

        name_error = validate_dict(action, "name")
        hash_key_error = (validate_dict(action, "name", "c_hash_key") or
                          await _controller.check_computer_hash_key(action["username"], action["name"],
                                                                    action["hash_key"]))

        _computer = await _controller.get_computer_by_name(action["username"],
                                                           action["name"]) if not name_error else UnknownComputer
        # computer_error = _computer if Error.is_error(_computer) else None

        if method.access_level:
            if conn.access_level < method.access_level:
                return NotEnoughtAccessLevel.json_alone()

        return await method.call_method(_controller, conn, action)


class MethodBox(Enum):
    @classmethod
    async def find_and_validate(cls, _dict) -> Union[APIErrorList, Method, None]:
        for method in cls:
            if method.value.string == _dict["method"]:
                return method.value.validate(_dict)

    @classmethod
    async def or_validate(cls, _dict, *methods) -> Union[Method, APIErrorList, None]:
        for m in methods[:-1]:
            val = await m.find_and_validate(_dict)
            if isinstance(val, Method):
                return val
            if Error.is_error(val):
                return val
        return await methods[-1].find_and_validate(_dict)


class Methods(MethodBox):
    CONNECT = Method("computer.connect", "name", access_level=0)
    DISCONNECT = Method("computer.disconnect")
    PING = Method("computer.ping", access_level=0)
    PING_ERROR = Method("computer.ping_error", access_level=0)

    BUTTON_ADD = Method("computer.button.add", "name", "button_name", "button_text")
    BUTTON_CLICK = Method("computer.button.click", "name", "button_name")

    EVENTS = Method("computer.get_events", "name")
    INFO = Method("computer.get_info", "name")


class UserMethods(MethodBox):
    REGISTER = Method("user.register", "username", "password", access_level=0)
    GET_COMPUTERS = Method("user.ge0t_computers", "username", "password", access_level=0)
