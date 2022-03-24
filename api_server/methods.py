import computer
import connection

from controller import ComputerController

from typing import Union, List
from enum import Enum

from api_errors import Error,  APIError, APIErrorList, NameBusy, UnknownComputer, MethodNotFound
from api_errors import WrongHashKey, WrongLoginData, validate_dict, APIErrorInit

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

        def dec (callback):
            async def wrapper(controller, conn, action, *args, 
                **kwargs):

                computer = await controller.get_computer_by_name(
                                                            action["username"],
                                                            action["name"])

                if Error.is_error(computer) and raise_not_found:
                    return computer.json_alone()

                return await callback(controller, conn, action, *args, 
                        **kwargs, _computer=computer)
                                  
            return wrapper
        return dec


class Method:
    methods_callbacks = {}

    def __init__(self, string, *required_values, need_login: bool = True):
        self.string = string
        self.required_values = list(required_values)
        self.need_login = need_login

        if need_login:
            self.required_values.append("hash_key")

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
        print(cls.methods_callbacks)
        return await cls.methods_callbacks[method](controller, conn, action)


@Method.method_callback("computer.connect")
@MethodSupport.get_computer(False)
async def computer_connect(controller, conn, action: dict, _computer):
    print("connect")
    if not conn.is_user:
        return WrongLoginData.json_alone()

    if not Error.is_error(_computer):
        return NameBusy.json_alone()
    
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
    return {"result": _computer.json_events()}


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
        hash_key_error = (validate_dict(action, "name", "hash_key") or
                          await _controller.check_computer_hash_key(action["username"], action["name"], action["hash_key"]))

        computer = await _controller.get_computer_by_name(action["username"], action["name"]) if not name_error else UnknownComputer
        computer_error = computer if Error.is_error(computer) else None

        if method.need_login:
            if not conn.logged_with_password:
                if hash_key_error:
                    print(hash_key_error)
                    return hash_key_error.json_alone()
            if name_error:
                return name_error.json_alone()
            if computer_error:
                return computer_error.json_alone()

        return await method.call_method(_controller, conn, action)

        """if method == Methods.CONNECT:
            if not conn.is_user:
                return WrongLoginData.json_alone()

            if name_error:
                return name_error.json_alone()
            if not computer_error:
                return NameBusy.json_alone()

            new_hash_key = sha256((action["username"] + action["name"] + str(randint(0, 100))).encode()).hexdigest()

            print(f"New hash key: {new_hash_key}")

            computer: Computer = Computer(conn.login, action["name"], new_hash_key)

            if conn.login not in self.computers:
                self.computers[conn.login] = {}

            self.computers[computer.username][computer.name] = computer

            return {"result": True, "hash_key": new_hash_key}

        if method == Methods.PING:
            return {"result": True}

        if method == Methods.PING_ERROR:
            return APIError.json()

        if method == Methods.BUTTON_ADD:
            computer.add_button(action["button_name"], action["button_text"])

            return {"result": True}

        if method == Methods.BUTTON_CLICK:
            computer.button_click(action["button_name"])

            return {"result": True}

        if method == UserMethods.REGISTER:
            print("register")
            if not await self.db.new_u:"wser(action["username"], action["password"]):
                return NameBusy.json()

            return {"result": True}

        if method == UserMethods.GET_COMPUTERS:
            if action["username"] not in self.computers:
                return {"result": []}
            return {"result": [comp.json() for _, comp in self.computers[action["username"]].items()]}

        if method == Methods.INFO:
            return {"result": computer.json()}

        if method == Methods.EVENTS:
            return {"result": computer.json_events()}"""

        print(method, "Method not found!")


class MethodBox(Enum):
    @classmethod
    async def find_and_validate(cls, _dict) -> Union[APIErrorList, Method, None]:
        print(iter(cls))
        for method in cls:
            print("Method: ", method, type(method.value))
            if method.value.string == _dict["method"]:
                return method.value.validate(_dict)

    @classmethod
    async def or_validate(cls, _dict, *methods) -> Union[Method, APIErrorList, None]:
        for m in methods[:-1]:
            val = await m.find_and_validate(_dict)
            print("VAL: ", val)
            if isinstance(val, Method):
                return val
            if Error.is_error(val):
                return val
        return await methods[-1].find_and_validate(_dict)


class Methods(MethodBox):
    CONNECT = Method("computer.connect", "name", need_login=False)
    DISCONNECT = Method("computer.disconnect")
    PING = Method("computer.ping", need_login=False)
    PING_ERROR = Method("computer.ping_error", need_login=False)

    BUTTON_ADD = Method("computer.button.add", "name", "button_name", "button_text")
    BUTTON_CLICK = Method("computer.button.click", "name", "button_name")

    EVENTS = Method("computer.get_events", "name")
    INFO = Method("computer.get_info", "name")
    

class UserMethods(MethodBox):
    REGISTER = Method("user.register", "username", "password", need_login=False)
    GET_COMPUTERS = Method("user.ge0t_computers", "username", "password", need_login=False)
