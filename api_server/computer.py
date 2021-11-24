from threading import Thread
from time import sleep
from typing import Union, List, Dict

from database import Database

database = Database()


class ActionType:

    def __init__(self, action: str, str_type: str, 
            *need_args, secured: bool = False):
        self.action = action
        self.str_type = str_type
        self.need_args = need_args
        self.secured = secured

    def has_all_args(self, _dict) -> (bool, list):
        ret = []

        for arg in self.need_args:
            if arg not in _dict:
                ret.append(arg)

        return ret

    def gen_error_args(self, _dict):
        args = self.has_all_args(_dict)

        if len(args):
            return Action.gen_action("need_args", "error", args=args)

        if self.secured or "for_id" in _dict:
            if "hash_key" not in _dict:
                return Action.gen_action("need_hash_key", "error")

            user_hash_key = database.get_hash_key(_dict["user_name"])

            if user_hash_key is None:
                return Action.gen_action("hash_key_not_created", "error")

            if user_hash_key != _dict["hash_key"]:
                return Action.gen_action("wrong_hash_key", "error")

    def gen_action(self, **kwargs) -> dict:
        action = {"action": self.action, "type": self.str_type}
        action.update(kwargs)

        return action

    def __eq__(self, other):
        return self.str_type == other


class ActionTypeMethod(ActionType):
    def __init__(self, str_type: str, *need_args, secured: bool = False):
        super().__init__("method", str_type, *need_args, secured=secured)


class ActionTypeError(ActionType):
    def __init__(self, str_type: str, *need_args, secured: bool = False):
        super().__init__("error", str_type, *need_args, secured=secured)


class Action:
    action = ""

    @classmethod
    def gen_action(cls, action_type: Union[ActionType, str], _action: Union[str, None] = None, **kwargs) -> dict:
        str_type = action_type.str_type if isinstance(action_type, ActionType) else action_type

        action = {"action": cls.action if _action is None else _action, "type": str_type}
        action.update(kwargs)

        return action

    @classmethod
    def parse(cls, data: dict):
        attrs: Dict[str, ActionType] = cls.__dict__
        attrs.pop("__module__")
        attrs.pop("action")
        attrs.pop("__doc__")

        for i in attrs:
            action_type = attrs[i]

            if action_type == data["type"]:
                ret = action_type.gen_error_args(data)
                return ret if ret is not None else action_type


class Methods(Action):
    action = "method"

    COMPUTER_DISCONNECT = ActionTypeMethod(str_type="computer.disconnect")
    GET_COMPUTERS = ActionTypeMethod("computers.get_all")

    BUTTON_CLICK = ActionTypeMethod("button.click")
    BUTTON_ADD = ActionTypeMethod("button.add", "name", "text")
    BUTTON_DELETE = ActionTypeMethod("button.delete", "name")
    BUTTON_DELETE_ALL = ActionTypeMethod("button.delete_all")
    BUTTON_RESET_CUR_COUNTER = ActionTypeMethod("button.reset_cur_counter")


class Errors(Action):
    action = "error"

    NEED_ARGS = ActionTypeError("need_args")

    NEED_HASH_KEY = ActionTypeError("need_hash_key")
    WRONG_HASH_KEY = ActionTypeError("wrong_hash_key")
    HASH_KEY_NOT_CREATED = ActionTypeError("hash_key_not_created")

    USER_NOT_FOUND = ActionTypeError("user_not_found")

    COMPUTER_NOT_FOUND = ActionTypeError("computer_not_found")

class Button:
    def __init__(self, name, text):
        self.name = name
        self.text = text

        self.click_count = 0
        self.all_click_count = 0

    def click(self):
        self.click_count += 1

    def reset_cur_counter(self):
        self.all_click_count += self.click_count
        self.click_count = 0

    def gen_action(self, reset: bool = False):
        if reset:
            self.reset_cur_counter()

        return Methods.BUTTON_CLICK.gen_action(name=self.name, count=self.click_count)


class IComputer:
    def add_button(self, button_name: str, button_text: str):
        pass

    def press_button(self, button_name: str):
        pass

    def disconnect(self):
        pass

    def get_actions(self):
        pass


class BroadcastComputer(IComputer):
    def __init__(self, user_name, handler):
        self.user_name = user_name
        self.handler: ComputerHandler = handler

    def add_button(self, button_name: str, button_text: str):
        computers = self.handler.get_user_computers(self.user_name)
        for computer in computers:
            computer.add_button(button_name, button_text)

    def press_button(self, button_name: str):
        computers = self.handler.get_user_computers(self.user_name)
        for computer in computers:
            computer.press_button(button_name)

    def disconnect(self):
        computers = self.handler.get_user_computers(self.user_name)
        for computer in computers:
            computer.disconnect()


class Computer(IComputer):
    def __init__(self, user_name: str, handler, adr: str, name: str, _id: int):
        self.adr = adr
        self.id = _id
        self.name = name
        self.user_name = user_name
        self.handler: "ComputerHandler" = handler

        self.added_message = ""
        self.added_message_timeout = 0

        self.timeout = 20

        self.buttons: Dict[str, Button] = {}
        self.actions = []

    def add_button(self, button_name: str, button_text: str):
        self.buttons[button_name] = Button(button_name, button_text)

    def press_button(self, button_name):
        self.buttons[button_name].click()

    def disconnect(self):
        self.handler.disconnect(self.user_name, self.id)

    def checked(self):
        self.timeout = 20

    def parse_answer(self, data: dict):
        ret = self.parse_action(data)

        if "get_actions" in data and data["get_actions"]:
            ret.extend(self.get_actions())

        return ret

    def parse_action(self, data: dict) -> list:
        if "action" not in data:
            return []

        broadcast = False

        action = data["action"]

        if action == "broadcast_method":
            broadcast = True
            action = "method"

        ret = []

        if action == "method":
            val = Methods.parse(data)
            target_comp = self
            if "for_id" in data:
                target_comp = self.handler.get_computer(self.user_name, data["for_id"])
                if target_comp is None:
                    return [Errors.COMPUTER_NOT_FOUND.gen_action()]

            if isinstance(val, dict):
                return [val]

            if val == Methods.COMPUTER_DISCONNECT:
                if not broadcast:
                    target_comp.disconnect()
                return [{"action": ""}]

            elif Methods.BUTTON_ADD == val:
                if not broadcast:
                    target_comp.add_button(data["name"], data["text"])
                else:
                    self.handler.get_broadcast_computer(self.user_name).add_button(data["name"], data["text"])

            elif Methods.BUTTON_DELETE == val:
                if data["name"] in self.buttons:
                    del target_comp.buttons[data["name"]]
                else:
                    pass

            elif Methods.BUTTON_DELETE_ALL == val:
                for button_name in [_ for _ in self.buttons]:
                    del target_comp.buttons[button_name]

            elif val == Methods.BUTTON_CLICK:
                if not broadcast:
                    target_comp.press_button(data["name"])
                else:
                    self.handler.get_broadcast_computer(self.user_name).press_button(data["name"])

            elif val == Methods.GET_COMPUTERS:
                computers = {}
                for comp in self.handler.get_user_computers(self.user_name):
                    computers[comp.id] = {"name": comp.name,
                                          "buttons": [bt_name for bt_name in comp.buttons]
                                          }
                ret.append({"type": "method_result", "method": Methods.GET_COMPUTERS.str_type,
                            "computers": computers})

            return ret

    def get_actions(self) -> list:
        ret = []

        for button_name in self.buttons:
            button = self.buttons[button_name]
            if button.click_count:
                ret.append(button.gen_action())
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
                    if comp_adr == 0:
                        continue

                    comp = self.computers[user_i][comp_adr]

                    if comp.timeout > 0:
                        comp.timeout -= 5

    def connect(self, user_name: str, adr: str, name: str) -> Computer:
        if user_name not in self.computers:
            self.computers[user_name] = {}
            self.computers[user_name][0] = BroadcastComputer(user_name, self)

        comp_id = None
        for i in range(len(self.computers[user_name])):
            if i not in self.computers[user_name]:
                comp_id = i
                break
        if comp_id is None:
            comp_id = len(self.computers[user_name]) + 1

        self.computers[user_name][comp_id] = Computer(user_name, self, adr, name, comp_id)

        self.add_cached_id(user_name, adr, comp_id)

        return self.computers[user_name][comp_id]

    def disconnect(self, user_name: str, _id: int):
        self.clear_cached_id_for(user_name, _id)
        del self.computers[user_name][_id]

    def get_user_computers(self, user_name: str) -> List[Computer]:
        return [self.computers[user_name][i] for i in self.computers[user_name] if i != 0] \
            if user_name in self.computers else []

    def get_broadcast_computer(self, user_name: str) -> Union[BroadcastComputer, None]:
        if user_name in self.computers:
            return self.computers[user_name][0]

    def add_cached_id(self, user_name: str, adr: str, _id: int):
        """
        Add computer id to cache

        :param user_name: User name
        :param adr: Computer address
        :param _id: Computer id in this web app
        :return: None
        """

        if user_name not in self.cached_id:
            self.cached_id[user_name] = {}
        self.cached_id[user_name][adr] = _id

    def clear_cached_id(self, user_name: str):
        """
        Clear all cached ids for one user
        """
        if user_name in self.cached_id:
            del self.cached_id[user_name]

    def clear_cached_id_for(self, user_name: str, _id: int):
        """
        Clear cached id of one computer
        """

        if user_name not in self.cached_id:
            return

        if _id in self.cached_id[user_name]:
            del self.cached_id[user_name][_id]

    def clear_cached_id_all(self):
        """
        Clear cached ids for all users
        """

        for user_name in self.computers.copy():
            self.clear_cached_id(user_name)

    def get_computer(self, user_name: str, adr: str = None, _id: int = None,
                     create_new: bool = False, name: str = None) -> Union[Computer, None]:
        """
        Get computer Object

        :param user_name: User name
        :param adr: Computer address
        :param _id: Id of searched computer
        :param create_new: If computer not exists, he will be created
        :param name: Name of new computer (if create_new == True)
        :return: Computer or None
        """

        if user_name in self.computers:
            if _id is not None:
                print(self.computers[user_name])
                if _id in self.computers[user_name]:
                    return self.computers[user_name][_id]
                return None

            if user_name in self.cached_id:
                if adr in self.cached_id[user_name]:
                    _id = self.cached_id[user_name][adr]
                    if _id in self.computers[user_name]:
                        return self.computers[user_name][_id]
                    return None

            for comp in [self.computers[user_name][i] for i in self.computers[user_name]]:
                if comp.adr == adr:
                    self.add_cached_id(user_name, adr, comp.id)
                    return comp

        if create_new:
            return self.connect(user_name, adr, name)

        return None
