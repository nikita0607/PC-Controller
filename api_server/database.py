import aiohttp

from config import DATABASE_HOST

from random import choice
from typing import Union


class Database:

    def __init__(self):

        self.user_count = 0
        self.user_hash_cache = {}

    @staticmethod
    def is_user(login):
        pass

    def create_hash_key(self, user_name: str):
        hash_key = ""

        self.user_hash_cache[user_name] = hash_key

    def get_hash_key(self, user_name: str) -> Union[str, None]:
        if user_name in self.user_hash_cache:
            return self.user_hash_cache[user_name]

    @staticmethod
    def check_user(login, password):
        pass

    def new_user(self, login, password):
        pass