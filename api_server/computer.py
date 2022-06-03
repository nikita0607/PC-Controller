from typing import List, Dict, Union

from connection import Connection


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


