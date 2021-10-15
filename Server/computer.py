from threading import Thread
from time import sleep


class Action:
    type = ""

    @classmethod
    def gen_action(cls, action_value, **kwargs):
        action = {"type": cls.type, "value": action_value}
        action.update(kwargs)

        return action


class ComputerMethods(Action):
    type = "method"

    DISCONNECT = "computer.disconnect"


class ButtonMethods(Action):
    type = "method"

    CLICK = "button.click"
    ADD = "button.add"


class Errors(Action):
    type = "error"

    NEED_ARGS = "need_args"
    USER_NOT_FOUND = "user_not_found"


class Button:
    def __init__(self, name, text):
        self.name = name
        self.text = text
        self.click_count = 0

    def click(self): self.click_count += 1


class Computer:
    def __init__(self, user_name, handler, adr, name, _id):
        self.adr = adr
        self.id = _id
        self.name = name
        self.user_name = user_name
        self.handler: "ComputerHandler" = handler

        self.added_message = ""
        self.added_message_timeout = 0

        self.timeout = 20

        self.buttons = {}
        self.actions = []

    def press_button(self, button_name):
        self.buttons[button_name].click()

    def disconnect(self):
        del self.handler.computers[self.user_name][self.adr]

    def checked(self):
        self.timeout = 20

    def parse_answer(self, data: dict):
        ret = self.parse_action(data)

        if "get_next" in data and data["get_next"]:
            self.gen_answer(ret)

        return ret

    def parse_action(self, data: dict):
        if "type" not in data:
            return []

        _type = data["type"]

        ret = []

        if _type == "method":
            if data["method"] == ComputerMethods.DISCONNECT:
                self.disconnect()
                return {"type": ""}
            elif data["method"] == ButtonMethods.ADD:
                if "text" not in data or "name" not in data:
                    ret.append(Errors.gen_action(Errors.NEED_ARGS))
                else:
                    self.buttons[data["name"]] = Button(data["name"], data["text"])
            elif data["method"] == ButtonMethods.CLICK:
                if "name" not in data:
                    ret.append(Errors.gen_action(Errors.NEED_ARGS))
                else:
                    self.press_button(data["name"])

        return ret

    def gen_answer(self, ret):

        for button_name in self.buttons:
            button = self.buttons[button_name]
            if button.click_count:
                ret.append(
                    ButtonMethods.gen_action(ButtonMethods.CLICK, name=button_name, count=button.click_count)
                )
                button.click_count = 0

        return ret


class ComputerHandler:

    def __init__(self, debug=False):
        self.debug = debug
        self.computers = {}

    def run(self):
        Thread(target=self.checker, daemon=True).start()

    def checker(self):
        while True:
            sleep(5)

            computers = self.computers.copy()
            for user_i in computers:
                for comp_adr in computers[user_i]:
                    comp = self.computers[user_i][comp_adr]

                    if comp.timeout > 0:
                        comp.timeout -= 5

    def connection(self, user_name, adr, name) -> Computer:
        if user_name not in self.computers:
            self.computers[user_name] = {}

        comp_id = len(self.computers[user_name])
        self.computers[user_name][comp_id] = Computer(user_name, self, adr, name, comp_id)

        return self.computers[user_name][adr]

    def get_computers(self, user_name):
        return [self.computers[user_name][i] for i in self.computers[user_name]] if user_name in self.computers else []

    def get_computer_id(self, user_name, id) -> Computer | None:

        if user_name in self.computers and id in self.computers[user_name]:
            return self.computers[user_name][id]

        return None

    def get_computer(self, user_name, adr, create_new: bool = False, name: str = None) -> Computer | None:
        if user_name in self.computers:
            for comp in [self.computers[user_name][i] for i in self.computers[user_name]]:
                if comp.adr == adr:
                    return comp

        if create_new:
            return self.connection(user_name, adr, name)

        return None
