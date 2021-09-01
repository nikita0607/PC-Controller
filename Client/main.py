import json
import os
import requests

from time import sleep
from socket import gethostbyname_ex, gethostname


class App:
    def __init__(self):
        print(os.getcwd())
        if not os.path.isfile("config.json"):
            with open("config.json", "w") as file:
                json.dump({"server-ip": ["127.0.0.1", 25560], "user_name": "None", "name": "None"}, file)

        self.config = json.load(open("config.json"))
        print(self.config)

    def run(self):
        ip = self.config["server-ip"]
        data = {"name": self.config["name"],
                "user_name": self.config["user_name"],
                "adr": str(gethostbyname_ex(gethostname())[-1][0]),
                "disable": False}

        req = requests.post(f"http://{ip[0]}:{ip[1]}/a", data=data)
        print(req.text)

        answer = json.loads(req.text)
        if answer["type"] == "error":
            if answer["error"] == "user not found":
                print(f"Пользователь {data['user_name']} не существует!")
                return
                
        while True:
            sleep(5)
            req = requests.post(f"http://{ip[0]}:{ip[1]}/a", data=data)

            ret_data = json.loads(req.text)

            print(ret_data)

            if ret_data["disable"]:
                data["disable"] = True

                a = os.system("shutdown /s /t 1")

                print(a)

                requests.post(f"http://{ip[0]}:{ip[1]}/a", data=data)

                data["disable"] = False

                data["added_message"] = "Потом"

                req = requests.post(f"http://{ip[0]}:{ip[1]}/a", data=data)

                del data["added_message"]

                print("Ошибка выключения!")
                


if __name__ == '__main__':
    app = App()
    app.run()