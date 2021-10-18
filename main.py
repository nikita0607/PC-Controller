import flask
import functools

from flask import Flask, render_template, redirect, jsonify
from socket import gethostbyname_ex, gethostname

from computer import *
from database import Database
from logger import Logger


try:
    with open('config.json') as file:
        config = json.load(file)
except:
    with open('config.json', 'w') as file:
        file.write('{"ip": ""}')
    raise


app = Flask(__name__)
app.config['SECRET_KEY'] = "skzhef3720t92497tyasojgke4892035ui"

app_ip = config["ip"]  # gethostbyname_ex(gethostname())[-1][0]

debug = True

database = Database()
main_logger = Logger("Main")
comp_handler = ComputerHandler(True)


def check_login(check_user_login=False):
    def decorator(func):
        @functools.wraps(func)
        def wrap(*args, **kwargs):
            if "login" not in flask.session:
                return redirect("/login")

            if not database.is_user(flask.session["login"]):
                del flask.session["login"]
                return redirect("/login")

            if check_user_login and "user_name" in kwargs and flask.session["login"] != kwargs["user_name"]:
                return redirect("/")

            return func(*args, **kwargs)

        return wrap

    return decorator


@app.route("/", methods=["GET"])
@app.route("/<string:user_name>", methods=["GET"])
def main(user_name=None):
    if "login" not in flask.session:
        return render_template("main.html", logged=False, user_name=None, none=None)
    if not database.is_user(flask.session["login"]):
        del flask.session["login"]
        return render_template("main.html", logged=False, user_name=user_name, none=None)

    return render_template("main.html", logged=True, user_name=flask.session["login"], none=None)


@app.route("/login", methods=["POST", "GET"])
def login():
    if flask.request.method == "GET":
        return render_template("login.html", wrong=0, user_name=None, none=None)

    login, password = flask.request.form['login'], flask.request.form['password']

    if database.check_user(login, password):
        main_logger.log("Logger in with login: ", login)
        flask.session["login"] = login
        return redirect("/computers")
    else:
        return render_template("login.html", wrong=1, user_name=None, none=None)


@app.route("/logout")
def logout():
    if "login" not in flask.session:
        return redirect("/")

    del flask.session["login"]
    return redirect("/")


a_ru = ord("а")
a_eng = ord("a")
A_ru = ord("А")
A_eng = ord("A")

good_syms = "_*&?"

good_syms += "".join([chr(i) for i in range(a_ru, a_ru + 32)])
good_syms += "".join([chr(i) for i in range(a_eng, a_eng + 26)])
good_syms += "".join([chr(i) for i in range(A_ru, A_ru + 32)])
good_syms += "".join([chr(i) for i in range(A_eng, A_eng + 26)])
good_syms += "".join([str(i) for i in range(10)])


@app.route("/register", methods=["GET", "POST"])
def register():

    if flask.request.method == "GET":
        return render_template("register.html", user_name=None, none=None)

    login, password = flask.request.form['login'], flask.request.form['password']
    password_again = flask.request.form['password-again']

    login_error = password_error = 0

    if len(login) > 20 or len(login) < 5:
        login_error = 1
    elif len([sym for sym in login if sym not in good_syms]) > 0:
        login_error = 2
    elif database.is_user(login):
        login_error = 3

    if len(password) > 50 or len(password) < 6:
        password_error = 1
    elif len([sym for sym in login if sym not in good_syms]) > 0:
        password_error = 2
    elif password != password_again:
        password_error = 3

    if login_error or password_error:
        return render_template("register.html", login_error=login_error, password_error=password_error, user_name=None,
                               none=None)

    else:
        database.new_user(login, password)
        flask.session["login"] = login
        return redirect("/")


@app.route("/computers")
@check_login()
def _computers():
    return computers(flask.session['login'])


@app.route("/<string:user_name>/computers")
@check_login(True)
def computers(user_name):
    return render_template("computers.html", computers=comp_handler.get_computers(user_name), user_name=user_name,
                           port="5000", ip=app_ip, len=len, none=None)


@app.route("/<string:user_name>/computers/<string:addr>/button_click/<string:button_name>")
@check_login(True)
def button_click(user_name, addr, button_name):
    main_logger.log("Tap button: %s" % button_name, " ", addr, name=flask.session["login"])
    comp = comp_handler.get_computer(user_name, addr)

    if comp is not None:
        comp.press_button(button_name)
    else:
        main_logger.log("Computer not found!", addr, name=flask.session["login"])

    return redirect("/computers")


@app.route("/a", methods=["POST", "GET"])
def comp_connect():
    if flask.request.method == "GET":
        return "Only for computer connection!"

    data = flask.request.get_json()

    if not ("user_name" in data and
            "name" in data):
        return jsonify({"count": 1, "actions": [Errors.gen_action(Errors.NEED_ARGS)]})

    if not database.is_user(data["user_name"]):
        return jsonify({"count": 1, "actions": [Errors.gen_action(Errors.USER_NOT_FOUND)]})

    computer = comp_handler.get_computer(data['user_name'], flask.request.remote_addr, True, data["name"])
    computer.checked()

    parsed_answer = computer.parse_answer(data)

    if isinstance(parsed_answer, dict):
        parsed_answer = [parsed_answer]

    return jsonify({"count": len(parsed_answer), "actions": parsed_answer})


comp_handler.run()
app.run(debug=debug, host=app_ip)
