import sqlite3
import os
import time
from hashlib import sha256

from threading import Thread
from time import sleep


class Log:

    def __init__(self, logger_name="Unknown"):
        if not os.path.isfile("logs.log"):
            open("logs.log", "w").close()

        self.logger_name = logger_name

    def log(self, *args, name=None):
        if name is None:
            name = self.logger_name

        with open("logs.log", "a") as file:
            s = ""
            for _s in args:
                s += _s

            file.write(f"{time.strftime('%D %T')} {name}: {s}\n")


class Methods:

    BUTTON_CLICK = "button.click"
    BUTTON_ADD = "button.add"


class Types:

    ERROR = "error"
    ERROR_NEED_ARGS = "need_args"


class Button:
    def __init__(self, name, text):
        self.name = name
        self.text = text
        self.click_count = 0

    def click(self):
        self.click_count += 1


class Computer:

    def __init__(self, user_name, handler, adr, name):
        self.adr = adr
        self.name = name
        self.user_name = user_name
        self.handler: "ComputerHandler" = handler

        self.added_message = ""
        self.added_message_timeout = 0

        self.timeout = 20

        self.buttons = {}
        self.actions = []

    def press_button(self, button_name):
        self.buttons[button_name].click()

    def disconnect(self):
        del self.handler.computers[self.user_name][self.adr]

    def checked(self):
        self.timeout = 20

    def parse_answer(self, data: dict):
        ret = []
        if data["method"] == "computer.disconnect":
            self.disconnect()

            return {"type": ""}

        elif data["method"] == Methods.BUTTON_ADD:
            if "text" not in data or "name" not in data:
                ret.append({"type": Types.ERROR, "error": Types.ERROR_NEED_ARGS})
            else:
                self.buttons[data["name"]] = Button(data["name"], data["text"])

        if "get_next" in data and data["get_next"]:
            self.gen_answer(ret)

        return ret

    def gen_answer(self, ret):

        for button_name, button in enumerate(self.buttons):
            if button.click_count:
                ret.append({"type": Methods.BUTTON_CLICK, "name": button_name, "count": button.click_count})
                button.click_count = 0

        return ret


class ComputerHandler:

    def __init__(self, debug=False):
        self.debug = debug
        self.computers = {}

    def run(self):
        Thread(target=self.checker, daemon=True).start()

    def checker(self):
        while True:
            sleep(5)

            comp_i = 0
            for user_i in self.computers.copy():
                while comp_i < len(self.computers):
                    comp = self.computers[user_i][comp_i]

                    if comp.timeout > 0:
                        comp.timeout -= 5

                    comp_i += 1

    def connection(self, user_name, adr, name):
        if user_name not in self.computers:
            self.computers[user_name] = []
        self.computers[user_name].append(Computer(self, user_name, adr, name))

    def get_computers(self, user_name):
        return self.computers[user_name] if user_name in self.computers else []

    def get_computer(self, user_name, adr) -> Computer or None:
        if user_name in self.computers:
            for comp in self.computers[user_name]:
                if comp.adr == adr:
                    return comp

        return None


class Database:

    def __init__(self):
        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("CREATE TABLE IF NOT EXISTS users (login, password)")

    @staticmethod
    def is_user(login):
        login = sha256(login.encode()).hexdigest()

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("SELECT * FROM users WHERE login=?", (login,))

            if sql.fetchone() is not None:
                return True

            return False

    @staticmethod
    def check_user(login, password):
        login, password = sha256(login.encode()).hexdigest(), sha256(password.encode()).hexdigest()
        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("SELECT * FROM users WHERE login=?", (login,))

            user = sql.fetchone()
            print(login)
            if user is None or user[1] != password:
                return False

            return True

    def new_user(self, login, password):
        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            if self.is_user(login):
                return False
            login, password = sha256(login.encode()).hexdigest(), sha256(password.encode()).hexdigest()
            print(login)
            sql.execute("INSERT INTO users VALUES (?, ?)", (login, password))

            return True
