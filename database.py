import sqlite3

from hashlib import sha256


class Database:

    def __init__(self):

        self.user_count = 0

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("CREATE TABLE IF NOT EXISTS users (login, password, id INT)")

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
            sql.execute("INSERT INTO users VALUES (?, ?, ?)", (login, password, self.user_count))

            self.user_count += 1

            return True