import asyncio

from connection import Connection
from api_errors import APIError, APIErrorList, NameBusy, UnknownComputer, WrongHashKey, validate_dict
from database import Database

from hashlib import sha256
from random import randint


class Method:
    def __init__(self, string, *required_values, need_hash_key: bool = True):
        self.string = string
        self.required_values = list(required_values)

        if need_hash_key:
            self.required_values.append("hash_key")

    def __str__(self):
        return self.string

    def __eq__(self, other):
        return str(self) == other

    def validate(self, _dict: dict) -> APIErrorList:
        res = validate_dict(_dict, *self.required_values)
        return res if res else self


class Methods:
    CONNECT = Method("computer.connect", "name", need_hash_key=False)
    PING = Method("computer.ping", need_hash_key=False)
    PING_ERROR = Method("computer.ping_error", need_hash_key=False)

    BUTTON_ADD = Method("computer.button.add", "username", "name", "button_name", "button_text")
    BUTTON_CLICK = Method("computer.button.click", "username", "name", "button_name")

    @classmethod
    def find_and_validate(cls, _dict) -> APIErrorList | Method | None:
        methods: list[Method] = [cls.__dict__[i] for i in cls.__dict__ if isinstance(cls.__dict__[i], Method)]

        for method in methods:
            if method.string == _dict["method"]:
                return method.validate(_dict)

            
class UserMethods(Methods):
    REGISTER = Method("user.register", "username", "password", need_hash_key=False)
    GET_COMPUTERS = Method("user.get_computers", "username", "password", need_hash_key=False)


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
        self.events = []

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

    def to_dict(self):
        return {"name": self.name, "buttons": self.buttons}
    

class ComputerController:
    def __init__(self):
        self.computers: dict[str, dict[str, Computer]] = {}
        self.db = Database()

    def get_computer_by_name(self, username: str, name: str) -> Computer | APIError:
        if username in self.computers and name in self.computers[username]:
            return self.computers[username][name]
        return UnknownComputer.to_dict()

    def check_computer_hash_key(self, username: str, name: str, hash_key: str) -> APIError | None:
        _comp = self.get_computer_by_name(username, name)

        if isinstance(_comp, APIError):
            return _comp
        
        if hash_key != _comp.hash_key:
            return WrongHashKey.to_dict()

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

        computer = self.get_computer_by_name(action["username"], action["name"])
        computer_error = computer if isinstance(computer, APIError) else None
        
        if method == Methods.CONNECT:
            if name_error:
                return name_error.to_dict()
            if not self.get_computer_by_name(action["username"], action["name"]):
                return NameBusy.to_dict()
            new_hash_key = sha256((action["username"]+action["name"]+str(randint(0, 100))).encode()).hexdigest()

            print(f"New hash key: {new_hash_key}")

            computer: Computer = Computer(action["username"], action["name"], new_hash_key)
            self.computers[computer.username][computer.name] = computer

            return {"result": True}

        if method == Methods.PING:
            return {"result": True}

        if method == Methods.PING_ERROR:
            return APIError.to_dict()

        if method == Methods.BUTTON_ADD:
            if hash_key_error:
                return hash_key_error.to_dict()
            if name_error:
                return name_error.to_dict()
            if computer_error:
                return computer_error.to_dict()

            computer.add_button(action["button_name"], action["button_text"])

            return {"result": True}

        if method == Methods.BUTTON_CLICK:
            if hash_key_error:
                return hash_key_error.to_dict()
            if name_error:
                return name_error.to_dict()
            if computer_error:
                return computer_error.to_dict()
            
            computer.click(action["button_name"])
            
            return {"result": True}

        if method == UserMethods.REGISTER:
            if not self.db.new_user(action["username"], action["password"]):
                return NameBusy.to_dict()

            return {"result": True}

        if method == UserMethods.GET_COMPUTERS:
            if action["username"] not in self.computers:
                return {"result": []}
            return {"result": [comp.to_dict() for comp in self.computers[action["username"]]]}


if __name__ == '__main__':  
    error = Methods.find_and_validate({"method": "computer.connect", "name": "Test"})
    if isinstance(error, APIErrorList):
        print(error.to_dict())
    print(error)