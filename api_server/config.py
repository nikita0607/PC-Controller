import os


def get_from_env(var):
    try:
        val = os.environ[var]
    except:
        raise ValueError(f"{var} is not in ENV!")

DEBUG = False

HOST = get_from_env("API_HOST")
PORT = get_from_env("API_PORT")

DATABASE_HOST = get_from_env("DATABASE_HOST")
DATABASE_PORT = get_from_env("DATABASE_PORT")
