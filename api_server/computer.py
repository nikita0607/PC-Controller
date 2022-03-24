import asyncio

from connection import Connection

from api_errors import Error,  APIError, APIErrorList, NameBusy, UnknownComputer, MethodNotFound
from api_errors import WrongHashKey, WrongLoginData, validate_dict, APIErrorInit

from database import Database

from hashlib import sha256
from random import randint


class EventValue:
    def __init__(self, default_value=None):
        self.value = default_value

    def __get__(self, *args):
        return self.value


class Event:
    type = "unknown"

    def __init__(self, _id: int):
        self.id = _id

    def to_dict(self) -> dict:
        _dict = {i: getattr(self, i) for i in self.__dict__ if isinstance(self.__dict__[i], EventValue)}
        _dict["type"] = self.type

        return _dict


class ButtonClickEvent(Event):
    type = "button_click"

    def __init__(self, _id: int, click_count=0):
        super().__init__(_id)
        self.click_count = EventValue(0)

    def add_click(self):
        self.click_count.value += 1


class Computer:
    def __init__(self, username: str, name: str, hash_key: str):
        self.username = username
        self.name = name
        self.hash_key = hash_key

        self.buttons: dict[str, str] = {}
        self.events: list[Event | ButtonClickEvent] = []

    def add_button(self, name: str, text: str) -> None:
        self.buttons[name] = text

    def get_new_id(self) -> int:
        return len(self.events) + 1

    def button_click(self, button_name: str) -> bool:
        if button_name in self.buttons:
            if len(self.events) and isinstance(self.events[-1], ButtonClickEvent):
                self.events[-1].add_click()
            else:
                self.events.append(ButtonClickEvent(self.get_new_id()))
                self.events[-1].add_click()
            return True
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
                _events.append(event.to_dict())

        return _events

    def clear_events(self):
        self.events.clear()


