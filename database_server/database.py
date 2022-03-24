import sqlite3

from hashlib import sha256
from random import choice
from typing import Union, List


class Database:

    def __init__(self):

        self.user_count = 0
        self.user_hash_cache = {}

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("CREATE TABLE IF NOT EXISTS users (login, password, id INT, hash_keys)")

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("SELECT COUNT(*) FROM users")
            self.user_count = sql.fetchone()[0]

    @staticmethod
    def check_user_login(login):
        login = sha256(login.encode()).hexdigest()

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("SELECT * FROM users WHERE login=?", (login,))

            if sql.fetchone() is not None:
                return True

            return False

    @staticmethod
    def create_hash_key(user_name: str) -> str:
        with sqlite3.connect("database.db") as db:
            sql = db.cursor()
            hash_key = sha256(choice("kadvfiuawvfakt4jm").encode()).hexdigest()
            login = sha256(user_name.encode()).hexdigest()

            sql.execute("SELECT hash_keys FROM users WHERE user_name=?", (user_name,))
            hash_keys = sql.fetchone()[0] + f"  {hash_key}"

            sql.execute("UPDATE users SET hash_keys=? WHERE login=?", (hash_keys, login))

        return hash_key

    @staticmethod
    def get_hash_keys(user_name) -> List[str]:
        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("SELECT hash_keys FROM users WHERE login=?", (sha256(user_name.encode()).hexdigest(),))
            hash_keys = sql.fetchone()[0].split("  ")

        return hash_keys

    @staticmethod
    def check_hash_key(user_name: str, hash_key: str) -> bool:
        hash_keys = Database.get_hash_keys(user_name)

        if hash_key in hash_keys:
            return True
        return False

    @staticmethod
    def check_user(login, password) -> bool:
        login, password = sha256(login.encode()).hexdigest(), sha256(password.encode()).hexdigest()
        print(login, password)
        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("SELECT * FROM users WHERE login=?", (login,))

            user = sql.fetchone()
            print(login)
            print(user)
            if user is None or user[1] != password:
                return False
            print("GOOD")
            return True

    def new_user(self, login, password):
        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            if self.check_user_login(login):
                print("It's real user")
                return False
            
            login, password = sha256(login.encode()).hexdigest(), sha256(password.encode()).hexdigest()
            print(login)
            sql.execute("INSERT INTO users VALUES (?, ?, ?, '')", (login, password, self.user_count))

            self.user_count += 1

        return True
