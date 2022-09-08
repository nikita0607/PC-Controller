import asyncio

from typing import List, Dict, Union, Type

from connection import Connection

from database import Database

from api_errors import Error,  APIError, APIErrorList, NameBusy, UnknownComputer, MethodNotFound
from api_errors import WrongHashKey, WrongLoginData, validate_dict, APIErrorInit

from hashlib import sha256
from random import randint


class EventValue:
    def __init__(self, default_value=None):
        self.value = default_value

    def __get__(self, *args):
        return self.value

    def json(self):
        return self.value


class Event:
    type = "unknown"

    def __init__(self, _id: int):
        self.id = _id

    def json(self) -> dict:
        _dict = {i: getattr(self, i).json() for i in self.__dict__ if isinstance(self.__dict__[i], EventValue)}
        _dict["type"] = self.type
        _dict["id"] = self.id

        return _dict


class ButtonClickEvent(Event):
    type = "button_click"

    def __init__(self, _id: int, button_name, click_count=0):
        super().__init__(_id)
        self.name = EventValue(button_name)


class Computer:
    def __init__(self, username: str, name: str, hash_key: str):
        self.username = username
        self.name = name
        self.hash_key = hash_key

        self.buttons: Dict[str, str] = {}
        self.events: List[Union[Event | ButtonClickEvent]] = []

    def add_button(self, name: str, text: str) -> None:
        self.buttons[name] = text

    def get_new_id(self) -> int:
        return len(self.events) + 1

    def button_click(self, button_name: str) -> bool:
        if button_name in self.buttons:
            self.events.append(ButtonClickEvent(self.get_new_id(), button_name))
        return False

    def json(self):
        return {"name": self.name, "buttons": self.buttons}

    def json_events(self, start_id=0, count=10):
        _events = []
        _count = 0
        for event in self.events:
            if _count > count:
                break
            if event.id >= start_id:
                _events.append(event.json())
                count += 1

        return _events

    def clear_events(self):
        self.events.clear()


class ComputerController:
    this = None
    _init = False

    def __new__(cls, *args, **kwargs):
        if not cls.this:
            cls.this = super().__new__(cls)
        return cls.this

    def __init__(self):
        if self._init:
            return
        
        self._init = True

        self.computers: Dict[str, Dict[str, Computer]] = {}
        self.db = Database()

    async def get_computer_by_name(self, username: str, name: str) -> Union[Computer, Type[UnknownComputer]]:
        if username in self.computers and name in self.computers[username]:
            return self.computers[username][name]
        return UnknownComputer

    async def get_computer_with_hashkey(self, username: str, name: str, c_hash_key: str) -> Union[Computer, Type[APIError]]:
        _computer = await self.get_computer_by_name(username, name)
        return _computer if _computer.hash_key == c_hash_key else WrongHashKey

    async def disconnect_computer(self, username, name):
        del self.computers[username][name]

    async def connect_computer(self, username, name):
        if username not in self.computers:
            self.computers[username] = {}
        hash_key = sha256((username + name + str(randint(0, 100))).encode()).hexdigest()
        self.computers[username][name] = Computer(username, name, hash_key)
        return self.computers[username][name]

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
