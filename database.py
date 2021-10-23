import sqlite3

from hashlib import sha256
from random import choice
from typing import Union


class Database:

    def __init__(self):

        self.user_count = 0
        self.user_hash_cache = {}

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("CREATE TABLE IF NOT EXISTS users (login, password, id INT, hash_key)")

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("SELECT COUNT(*) FROM users")
            self.user_count = sql.fetchone()[0]
            print(self.user_count)

    @staticmethod
    def is_user(login):
        login = sha256(login.encode()).hexdigest()

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("SELECT * FROM users WHERE login=?", (login,))

            if sql.fetchone() is not None:
                return True

            return False

    def create_hash_key(self, user_name: str):
        with sqlite3.connect("database.db") as db:
            sql = db.cursor()
            hash_key = sha256(choice("kadvfiuawvfakt4jm").encode()).hexdigest()

            sql.execute("UPDATE users SET hash_key=? WHERE login=?", (hash_key, sha256(user_name.encode()).hexdigest(),))

            self.user_hash_cache[user_name] = hash_key

    def get_hash_key(self, user_name: str) -> Union[str, None]:
        if user_name in self.user_hash_cache:
            return self.user_hash_cache[user_name]

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("SELECT hash_key FROM users WHERE login=?", (sha256(user_name.encode()).hexdigest(),))
            hash_key = sql.fetchone()[0]

            if hash_key != "":
                return hash_key
            else:
                return None

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
            sql.execute("INSERT INTO users VALUES (?, ?, ?, '')", (login, password, self.user_count))

            self.user_count += 1

            return True
