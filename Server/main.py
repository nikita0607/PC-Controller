import flask
import functools

from flask import Flask, render_template, redirect, jsonify
from socket import gethostbyname_ex, gethostname

from requests.sessions import session
from classes import *


app = Flask(__name__)
app.config['SECRET_KEY'] = "skzhef3720t92497tyasojgke4892035ui"

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
    return render_template("computers.html", computers=comp_handler.get_computers(user_name), user_name=user_name, len=len, none=None)


@app.route("/<string:user_name>/computers/<string:adr>/disable")
@check_login(True)
def dis_comp(user_name, adr):
    main_logger.log("Disabling computer with adress: ", adr, name=flask.session["login"])
    comp_handler.get_computer(user_name, adr).disable()

    return redirect("/computers")


@app.route("/<string:user_name>/computers/disable_all")
@check_login(True)
def dis_all(user_name):

    for comp in comp_handler.get_computers(user_name):
        comp.disable()

    main_logger.log("Disabling all computers", name=flask.session["login"])

    return redirect("/computers")


@app.route("/a", methods=["POST", "GET"])
def _comp_connect():
    if flask.request.method == "GET":
        return "Only for computer connection!"

    data = {}

    for i in flask.request.get_data().decode().split("&"):
        _s = i.split("=")
        data[_s[0]] = _s[1]
    print(data)

    if not database.is_user(data["user_name"]):
        return jsonify({"type": "error", "error": "user not found"})

    if comp_handler.get_computer(data['user_name'], data["adr"]) is not None:
        comp = comp_handler.get_computer(data['user_name'], data["adr"])
        comp.checked()

        if data["disable"] == "True":
            comp.set_disabled()

            return "Goodbye!"

        if "added_message" in data:
            comp.set_added_message(data["added_message"], 
            (data["added_message_timeout"] if "added_message_timeout" in data else 5))

        return jsonify({"type": "normal_answer", "new_connection": False, "disable": comp.disabling})

    else:
        comp_handler.connection(data['user_name'], data["adr"], data["name"])
        return jsonify({"type": "normal_answer", "new_connection": True})


comp_handler.run()
app.run(debug=debug, host=gethostbyname_ex(gethostname())[-1][0])