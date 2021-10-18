import os
import time

from threading import Thread
from time import sleep


class GlobalLogger:
    def __init__(self):
        self.max_size = 100
        self.logs_count = 0
        self.stack = []

        if not os.path.isdir("logs"):
            os.mkdir("logs")

        if not os.path.isfile("logs/logs.log"):
            open("logs.log", "w").close()

        for file in os.listdir("logs"):
            if file.startswith("oldlog_"):
                self.logs_count += 1

    def add_log_info(self, info: str):
        self.stack.append(info)

    def set_max_size(self, size: int):
        self.max_size = size

    def run(self):
        cur_str = 0

        while True:
            sleep(0.1)

            with open("logs/logs.log", "a") as file:
                while len(self.stack):
                    log_info = self.stack.pop(0)

                    file.write(log_info)

                    cur_str += 1

                    if cur_str > self.max_size:
                        break

            if cur_str > self.max_size:
                os.rename("logs/logs.log", f"logs/oldlogs_{self.logs_count}")

                self.logs_count += 1
                cur_str = 0


global_logger = GlobalLogger()
Thread(daemon=True, target=global_logger.run).start()


class Logger:

    def __init__(self, logger_name="Unknown"):
        self.logger_name = logger_name
        self.global_logger = global_logger

    def log(self, *args, name=None):
        if name is None:
            name = self.logger_name

        s = ""
        for _s in args:
            s += _s

        self.global_logger.add_log_info(f"{time.strftime('%D %T')} {name}: {s}\n")