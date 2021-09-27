import json
import os
import requests

from time import sleep
from socket import gethostbyname_ex, gethostname

if not os.path.isfile("config.json"):
    with open("config.json", "w") as file:
        json.dump({"server-ip": ["192.168.0.1", 5000], "user_name": "None", "computer_name": "None"}, file)


class API:

    def __init__(self, user_name, computer_name, server_address):
        self.user_name = user_name
        self.computer_name = computer_name

        if isinstance(server_address, str):
            self.server_address = server_address
        else:
            self.server_address = f"{server_address[0]}:{server_address[1]}"
            print(self.server_address)

        self.address = str(gethostbyname_ex(gethostname())[-1][0])

    def call_method(self, method="ping", get_next=False, **kwargs):
        data = {"user_name": self.user_name,
                "computer_name": self.computer_name,
                "get_next": get_next,
                "adr": self.address,
                "method": method}

        for i in kwargs:
            data[i] = kwargs[i]

        req = requests.post(f"http://{self.server_address}/a", data=data)
        return req.json()



class App:
    def __init__(self):
        print(os.getcwd())

        self.config = json.load(open("config.json"))
        print(self.config)

    def run(self):
        api = API(self.config["user_name"], self.config["computer_name"], self.config["server-ip"])

        answer = api.call_method("button.add", name="disable", text="Отключить")

        if answer["count"] and answer[0]["type"] == "error":
            if answer[0]["error"] == "user not found":
                print(f"Пользователь {api.user_name} не существует!")
                return
                
        while True:
            sleep(5)

            ret_data = api.call_method(get_next=True)

            for type in ret_data["actions"]:
                if type["type"] == "button.click":
                    if type["name"] == "disable":
                        api.call_method("computer.disconnect")
                        #a = os.system("shutdown /s /t 1")
                        # print(a)
                        pass


if __name__ == '__main__':
    app = App()
    app.run()