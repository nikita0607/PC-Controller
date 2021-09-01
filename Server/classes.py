import sqlite3
import socket
import os
import time

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

            file.write(f"{time.strftime('%D %T')} {name}: {s}/n")


class Computer:

    def __init__(self, handler, adr, name):
        self.adr = adr
        self.name = name
        self.handler = handler

        self.added_message = ""
        self.added_message_timeout = 0

        self.timeout = 20

        self.disabled = False
        self.disabling = False

    def disable(self):
        self.disabling = True

    def set_disabled(self):
        self.disabled = True
        self.disabling = False

    def checked(self):
        self.timeout = 20
        self.disabled = False

    def set_added_message(self, message, timeout: int = 10):
        self.added_message = message
        self.added_message_timeout = timeout


class ComputerHandler(socket.socket):

    def __init__(self, debug=False):
        super().__init__()

        self.debug = debug
        self.computers = {}

    def run(self):
        Thread(target=self.checker, daemon=True).start()

    def checker(self):
        while True:
            sleep(5)

            comp_i = 0
            for user_i in self.computers:
                while comp_i < len(self.computers):
                    comp = self.computers[user_i][comp_i]

                    if comp.timeout > 0:
                        comp.timeout -= 5

                    comp_i += 1

    def connection(self, user_name, adr, name):
        if user_name not in self.computers:
            self.computers[user_name] = []
        self.computers[user_name].append(Computer(self, adr, name))

    def get_computers(self, user_name):
        return (self.computers[user_name] if user_name in self.computers else [])

    def get_computer(self, user_name, adr) -> Computer:
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

    def is_user(self, login):
        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("SELECT * FROM users WHERE login=?", (login,))

            if sql.fetchone() is not None:
                return True

            return False

    def check_user(self, login, password):
        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("SELECT * FROM users WHERE login=?", (login,))

            user = sql.fetchone()
            if user is None or user[1] != password:
                return False

            return True

    def new_user(self, login, password):
        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            if self.is_user(login):
                return False

            sql.execute("INSERT INTO users VALUES (?, ?)", (login, password))

            return True
