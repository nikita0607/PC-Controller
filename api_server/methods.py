from typing import Union, List
from enum import Enum

from hashlib import sha256
from random import randint

import connection

from computers import Computer, ComputerController

from debug import d_print

from api_errors import Error, APIError, APIErrorList, NameBusy, UnknownComputer, MethodNotFound
from api_errors import WrongHashKey, WrongLoginData, validate_dict, APIErrorInit
from api_errors import NotEnoughtAccessLevel

from database import Database


class MethodSupport:
    @staticmethod
    def get_database(callback):
        async def wrapper(conn, action, *args,
                          **kwargs):
            return await callback(conn, action, *args, **kwargs,
                                  database=Database())

        return wrapper

    @staticmethod
    def get_computer(raise_not_found: bool = True):
        """ Decorator return computer with recieved 'username' and 'name' """

        def dec(callback):
            async def wrapper(conn, action, *args, **kwargs):
                controller = ComputerController()

                if "for_name" in action:

                    _computer = await controller.get_computer_by_name(
                        action["username"],
                        action["for_name"])

                elif "c_hash_key" in action:
                    _computer = await controller.get_computer_with_hashkey(
                        action["username"],
                        action["name"],
                        action["c_hash_key"])
                else:
                    return WrongHashKey.json_alone()

                if Error.is_error(_computer) and raise_not_found:
                    return _computer.json_alone()

                return await callback(controller, conn, action, *args,
                                      **kwargs, _computer=_computer)

            return wrapper

        return dec

    @staticmethod
    def get_controller(controller_first: bool = False):
        def dec(callback):
            def wrapper(conn, action, *args, **kwargs):
                if controller_first:
                    return callback(ComputerController(), conn, action, *args, **kwargs)
                return callback(conn, action, *args, **kwargs, controller=ComputerController())
            return wrapper
        return dec


class Method:
    def __init__(self, string, *required_values, access_level: int = 1):
        self.string = string
        self.required_values = list(required_values)
        self.access_level = access_level
        self.callback = None
    
    def __str__(self):
        return self.string

    def __eq__(self, other):
        return str(self) == other

    def validate(self, _dict: dict) -> APIErrorList:
        res = validate_dict(_dict, *self.required_values)
        return res if res else self

    def method_callback(self, callback):
        self.callback = callback
        return callback

    async def call(self, conn, action: dict):
        return await self.callback(conn, action)


class MethodBox(Enum):
    @classmethod
    def check(cls) -> bool:
        return all(map(lambda cl: cl.value.callback, cls))


class Methods:
    method_boxes = {}
    
    @classmethod
    def method_box(cls, prefix: str):
        def dec(mbox):
            cls.add_method_box(prefix, mbox)
            return callback
        return dec

    @classmethod
    async def find_and_validate(cls, _dict) -> Union[APIErrorList, Method, None]:
        str_method = _dict["method"]
        prefix, str_method = str_method.split('.')

        for method in cls.method_boxes[prefix]:
            if method.value.string == str_method:
                return method.value.validate(_dict)

    @classmethod
    def check(cls) -> Union[MethodBox, None]:
        for _, mbox in cls.method_boxes.items():
            if not mbox.check():
                return cls


@Methods.method_box("user")
class ComputerMethods(MethodBox):
    CONNECT = Method("connect", "name", access_level=0)
    DISCONNECT = Method("disconnect")
    PING = Method("ping", access_level=0)
    PING_ERROR = Method("ping_error", access_level=0)
    BUTTON_ADD = Method("button.add", "name", "button_name", "button_text")
    BUTTON_CLICK = Method("button.click", "name", "button_name")

    GET_EVENTS = Method("get_events", "name")
    GET_INFO = Method("get_info", "name")
    TEST = Method("test")


@Methods.method_box("user")
class UserMethods(MethodBox):
    REGISTER = Method("register", "username", "password", access_level=0)
    GET_COMPUTERS = Method("get_computers", "username", "password", access_level=0)


@ComputerMethods.CONNECT.value.method_callback
@MethodSupport.get_controller(True)
async def computer_connect(controller: ComputerController, conn, action: dict):
    print("connect")
    if not conn.registered_user:
        return WrongLoginData.json_alone("username")

    if await controller.check_computer(action["username"], action["name"]) is None:
        return NameBusy.json_alone("name")

    controller.connect_computer(action["username"], action["name"])

    return {"result": True, "c_hash_key": new_hash_key}


@ComputerMethods.PING.value.method_callback
async def ping(*args, **kwargs):
    return {"result": True}


@ComputerMethods.PING_ERROR.value.method_callback
async def ping_error(*args, **kwargs):
    return APIError.json_alone()


@ComputerMethods.BUTTON_ADD.value.method_callback
@MethodSupport.get_computer()
async def computer_add_button(conn, action, _computer: Computer):
    _computer.add_button(action["button_name"], action["button_text"])
    return {"result": True}


@ComputerMethods.BUTTON_CLICK.value.method_callback
@MethodSupport.get_computer()
async def computer_add_button(conn, action, _computer: Computer):
    _computer.button_click(action["button_name"])
    return {"result": True}


@UserMethods.REGISTER.value.method_callback
@MethodSupport.get_database
async def user_register(conn, action, database: Database):
    if conn.registered_user:
        return NameBusy.json_alone()

    await database.new_user(conn.login, action["password"])
    return {"result": True}


@UserMethods.GET_COMPUTERS.value.method_callback
@MethodSupport.get_controller(True)
async def user_get_computers(controller: ComputerController, conn, action):
    if action["username"] not in controller.computers:
        return {"result": []}

    return {"result": [comp.json()
                       for _, comp in controller.computers[action["username"]].items()]}


@ComputerMethods.GET_INFO.value.method_callback
@MethodSupport.get_computer()
async def computer_info(controller, conn, action, _computer: Computer):
    return {"result": _computer.json()}


@ComputerMethods.GET_EVENTS.value.method_callback
@MethodSupport.get_computer()
async def get_events(conn, action, _computer: Computer):
    _id = action["start_id"] if "start_id" in action else 0
    return {"result": _computer.json_events(start_id=_id)}


@ComputerMethods.DISCONNECT.value.method_callback
@MethodSupport.get_computer()
@MethodSupport.get_controller(True)
async def disconnect(controller: ComputerController, conn,
                     action, _computer: Computer):
    await controller.disconnect_computer(_computer.username, _computer.name)
    return {"result": True}


class MethodParser:
    @staticmethod
    async def parse_action(conn: connection.Connection, action: dict):
        _method = action["method"]

        validate_result = await Methods.find_and_validate(_dict)

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

        if method.access_level:
            if "c_hash_key" in action:
                _error = _controller.check_computer_hash_key(action["username"], action["name"], action["c_hash_key"])
                if Error.is_error(_error):
                    return _error.json_alone()
            if conn.access_level < method.access_level:
                return NotEnoughtAccessLevel.json_alone()

        return await method.call_method(_controller, conn, action)

res = Methods.check()
if res:
    raise AttributeError(f"Not all methods in {res} has callback realisation")
