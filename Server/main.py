import flask
import functools

from flask import Flask, render_template, redirect, jsonify
from socket import gethostbyname_ex, gethostname

from requests.sessions import session
from classes import *


app = Flask(__name__)
app.config['SECRET_KEY'] = "skzhef3720t92497tyasojgke4892035ui"
app_ip = gethostbyname_ex(gethostname())[-1][0]


debug = True

database = Database()
main_logger = Log("Main")
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
        main_logger.log("Log in with login: ", login)
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
    errors = {"login_len_error": False,
              "login_sym_error": False,
              "login_registered": False,
              "password_len_error": False,
              "password_sym_error": False}

    if flask.request.method == "GET":
        return render_template("register.html", errors=errors, user_name=None, none=None)

    login, password = flask.request.form['login'], flask.request.form['password']

    if len(login) > 20 or len(login) < 5:
        errors["login_len_error"] = True
    if len([sym for sym in login if sym not in good_syms]) > 0:
        errors["login_sym_error"] = True
    if not [errors[error] for error in errors].count(True):
        if database.is_user(login):
            errors["login_registered"] = True

    if len(password) > 50 or len(password) < 6:
        errors["password_len_error"] = True
    if len([sym for sym in login if sym not in good_syms]) > 0:
        errors["password_sym_error"] = True

    if [errors[error] for error in errors].count(True):
        return render_template("register.html", errors=errors, user_name=None, none=None)

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


@app.route("/<string:user_name>/computers/<string:adr>/button_click/<string:button_name>")
@check_login(True)
def button_click(user_name, adr, button_name):
    main_logger.log("Tap button: %s" % button_name, adr, name=flask.session["login"])
    comp_handler.get_computer(user_name, adr).press_button(button_name)

    return redirect("/<string:user_name>/computers")


@app.route("/a", methods=["POST", "GET"])
def _comp_connect():
    if flask.request.method == "GET":
        return "Only for computer connection!"

    data = {}

    for i in flask.request.get_data().decode().split("&"):
        _s = i.split("=")
        data[_s[0]] = _s[1].replace("+", " ").replace("%21", "")
    print(data)

    if not database.is_user(data["user_name"]):
        return jsonify({"count": 1, "actions": [{"type": "error", "error": "user not found"}]})

    computer = comp_handler.get_computer(data['user_name'], data["adr"])
    if computer is not None:
        computer.checked()
        parsed_answer = computer.parse_answer(data)

        if isinstance(parsed_answer, dict):
            parsed_answer = [parsed_answer]

        return jsonify({"count": len(parsed_answer), "actions": parsed_answer})

    else:
        comp_handler.connection(data['user_name'], data["adr"], data["computer_name"])
        return jsonify({"count": 1, "actions": [{"type": "new_connection"}]})


comp_handler.run()
app.run(debug=debug, host=app_ip)