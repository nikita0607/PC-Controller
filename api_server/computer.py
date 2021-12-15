import asyncio

from connection import Connection

from api_errors import Error,  APIError, APIErrorList, NameBusy, UnknownComputer
from api_errors import WrongHashKey, WrongLoginData, validate_dict, APIErrorInit

from database import Database

from hashlib import sha256
from random import randint


class Method:
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


class Methods:
    CONNECT = Method("computer.connect", "name", need_login=False)
    PING = Method("computer.ping", need_login=False)
    PING_ERROR = Method("computer.ping_error", need_login=False)

    BUTTON_ADD = Method("computer.button.add", "name", "button_name", "button_text")
    BUTTON_CLICK = Method("computer.button.click", "name", "button_name")

    EVENTS = Method("computer.events", "name")

    @classmethod
    def find_and_validate(cls, _dict) -> APIErrorList | Method | None:
        methods: list[Method] = [cls.__dict__[i] for i in cls.__dict__ if isinstance(cls.__dict__[i], Method)]

        for method in methods:
            if method.string == _dict["method"]:
                return method.validate(_dict)


class UserMethods(Methods):
    REGISTER = Method("user.register", "username", "password", need_login=False)
    GET_COMPUTERS = Method("user.get_computers", "username", "password", need_login=False)


class EventValue:
    def __init__(self, default_value=None):
        self.value = default_value

    def __get__(self, *args):
        return self.value


class Event:
    def to_dict(self) -> dict:
        return {i: getattr(self, i) for i in self.__dict__ if isinstance(self.__dict__[i], EventValue)}


class ButtonClickEvent(Event):
    def __init__(self):
        self.click_count = EventValue(0)

    def add_click(self):
        self.click_count += 1


class Computer:
    def __init__(self, username: str, name: str, hash_key: str):
        self.username = username
        self.name = name
        self.hash_key = hash_key

        self.buttons: dict[str, str] = {}
        self.events: list[Event | ButtonClickEvent] = []

    def add_button(self, name: str, text: str) -> None:
        self.buttons[name] = text

    def button_click(self, button_name: str) -> bool:
        if button_name in self.buttons:
            if len(self.events) and isinstance(self.events[-1], ButtonClickEvent):
                self.events[-1].add_click()
            else:
                self.events.append(ButtonClickEvent())
            return True
        return False

    def json(self):
        return {"name": self.name, "buttons": self.buttons}

    def events(self):
        _events = []
        for event in self.events:
            _events.append(event.to_dict())

        return _events


class ComputerController:
    this = None

    def __new__(cls, *args, **kwargs):
        if not cls.this:
            cls.this = super().__new__(cls)
        return cls.this

    def __init__(self):
        self.computers: dict[str, dict[str, Computer]] = {}
        self.db = Database()

    async def get_computer_by_name(self, username: str, name: str) -> Computer | APIErrorInit:
        if username in self.computers and name in self.computers[username]:
            return self.computers[username][name]
        return UnknownComputer()

    async def check_computer_hash_key(self, username: str, name: str, hash_key: str) -> APIError | None:
        _comp = await self.get_computer_by_name(username, name)

        if Error.is_error(_comp):
            return _comp

        print(_comp)

        if hash_key != _comp.hash_key:
            return WrongHashKey

    async def parse_action(self, conn: Connection, action: dict):
        error = validate_dict(action, "method")

        if error:
            print("Error: ", error)
            return error

        _method = action["method"]

        validate_result = Methods.find_and_validate(action) or UserMethods.find_and_validate(action)

        if validate_result is None:
            pass

        if Error.is_error(validate_result):
            return validate_result.json_alone()

        method: Method = validate_result

        name_error = validate_dict(action, "name")
        hash_key_error = (validate_dict(action, "name", "hash_key") or
                          await self.check_computer_hash_key(action["username"], action["name"], action["hash_key"]))

        computer = await self.get_computer_by_name(action["username"], action["name"]) if not name_error else UnknownComputer
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

        if method == Methods.CONNECT:
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
            if not await self.db.new_user(action["username"], action["password"]):
                return NameBusy.json()

            return {"result": True}

        if method == UserMethods.GET_COMPUTERS:
            if action["username"] not in self.computers:
                return {"result": []}
            return {"result": [comp.json() for _, comp in self.computers[action["username"]].items()]}

        print(method, "Method not found!")


if __name__ == '__main__':
    error = Methods.find_and_validate({"method": "computer.connect", "name": "Test"})
    if Error.is_error(error):
        print(error.json())
    print(error)
