import aiohttp
import requests

from config import DATABASE_HOST

from random import choice
from typing import Union


class Database:
    db_object = None

    def __new__(cls):
        if cls.db_object is None:
            cls.db_object = cls.__init__()
        return cls.db_object

    def __init__(self):
        self.user_count = 0
        self.user_hash_cache = {}

        self.db_object = self

    @staticmethod
    async def check_user_login(login):
        data = {"action": "check_user_login", "login": login}

        async with aiohttp.ClientSession() as session:
            async with session.post(DATABASE_HOST, data=data) as resp:
                response = await resp.json()

                if "result" in response:
                    return response["result"]
                else:
                    print("Database 'check_user_login' ERROR!")
                    return False

    @staticmethod
    async def create_hash_key(user_name: str) -> str:
        data = {"action": "create_hash_key", "login": user_name}

        async with aiohttp.ClientSession() as session:
            async with session.post(DATABASE_HOST, json=data) as resp:
                response = await resp.json()

                if "result" in response:
                    return response["result"]
                else:
                    print("Database 'create_hash_key' ERROR!")
                    return ""

    @staticmethod
    async def get_hash_keys(user_name: str) -> list[str]:
        data = {"action": "get_hash_keys", "login": user_name}

        async with aiohttp.ClientSession() as session:
            async with session.post(DATABASE_HOST, json=data) as resp:
                response = await resp.json()

                if "result" in response:
                    return response["result"]
                else:
                    print("Database 'get_hash_keys' ERROR!")
                    return []

    @staticmethod
    async def check_hash_key(user_name: str, hash_key) -> bool:
        data = {"action": "check_hash_key", "login": user_name}

        async with aiohttp.ClientSession() as session:
            async with session.post(DATABASE_HOST, json=data) as resp:
                response = await resp.json()

                if "result" in response:
                    return response["result"]
                else:
                    print("Database 'check_hash_key' ERROR!")
                    return False

    @staticmethod
    async def check_user(login, password) -> bool:
        data = {"action": "check_user", "login": login, "password": password}

        async with aiohttp.ClientSession() as session:
            async with session.post(DATABASE_HOST, json=data) as resp:
                response = await resp.json()

                if "result" in response:
                    return response["result"]
                else:
                    print("Database 'check_user' ERROR!")
                    return False

    @staticmethod
    async def new_user(login, password) -> bool:
        data = {"action": "register", "login": login, "password": password}

        async with aiohttp.ClientSession() as session:
            async with session.post(DATABASE_HOST, json=data) as resp:
                response = await resp.json()

                if "result" in response:
                    return response["result"]
                else:
                    print("Database 'create_hash_key' ERROR!")
                    return False
