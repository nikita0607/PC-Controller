from threading import Thread
from time import sleep


class Action:
    action = ""

    @classmethod
    def gen_action(cls, action_value, **kwargs):
        action = {"action": cls.action, "type": action_value}
        action.update(kwargs)

        return action


class ComputerMethods(Action):
    action = "method"

    DISCONNECT = "computer.disconnect"


class ButtonMethods(Action):
    action = "method"

    CLICK = "button.click"
    ADD = "button.add"


class Errors(Action):
    action = "error"

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
        if "action" not in data:
            return []

        action = data["action"]

        ret = []

        if action == "method":
            if data["method"] == ComputerMethods.DISCONNECT:
                self.disconnect()
                return {"action": ""}
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

        self.cached_id = {}

    def run(self):
        Thread(target=self.checker, daemon=True).start()

    def checker(self):
        iters = 0

        while True:
            sleep(5)
            iters += 1

            if not iters % 100:
                self.clear_cached_id_all()

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

        self.add_cached_id(user_name, adr, comp_id)

        return self.computers[user_name][adr]

    def get_user_computers(self, user_name):
        return [self.computers[user_name][i] for i in self.computers[user_name]] if user_name in self.computers else []

    def add_cached_id(self, user_name: str, adr: str, id: str):
        """
        :param user_name: User name
        :param adr: Computer address
        :param id: Computer id in this web app
        :return: None

        Add computer id to cache
        """

        if user_name not in self.cached_id:
            self.cached_id[user_name] = {}
        self.cached_id[user_name][adr] = id

    def clear_cached_id(self, user_name):
        if user_name in self.cached_id:
            del self.cached_id[user_name]

    def clear_cached_id_all(self):
        for user_name in self.computers.copy():
            self.clear_cached_id(user_name)

    def get_computer(self, user_name, adr, create_new: bool = False, name: str = None) -> Computer | None:
        """
        :param user_name: User name
        :param adr: Computer address
        :param create_new: If computer not exists, he will be created
        :param name: Name of new computer (if create_new == True)
        :return: Computer or None
        """

        if user_name in self.computers:
            if user_name in self.cached_id:
                if adr in self.cached_id[user_name]:
                    return self.cached_id[user_name][adr]

            for comp in [self.computers[user_name][i] for i in self.computers[user_name]]:
                if comp.adr == adr:
                    self.add_cached_id(user_name, adr, comp.id)
                    return comp

        if create_new:
            return self.connection(user_name, adr, name)

        return None
