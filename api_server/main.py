import json

import flask

from flask import Flask, render_template, redirect, jsonify
from flask import request, session

from config import *

from computer import *


app = Flask(__name__)
app.config['SECRET_KEY'] = "skzhef3720t92497tyasojgke4892035ui"


@app.route("/api-doc")
def api_doc():
    return "Welcome to the doc!"


@app.route("/api", methods=["GET", "POST"])
def api():
    if request.method == "GET":
        return redirect("/api-doc")
    
    data = flask.request.get_json()

    if data is None:
        data = {}
    else:
        data = json.loads(data)

    print(data, type(data))

    if "user_name" in data:
        user_name = data["user_name"]
        flask.session["user_name"] = user_name
    elif "user_name" in flask.session:
        user_name = flask.session["user_name"]
    else:
        return jsonify({"count": 1, "actions": [Errors.gen_action(Errors.NEED_ARGS)]})

    name = flask.request.remote_addr
    if "name" in data:
        name = data["name"]
        flask.session["name"] = name
    elif "name" in flask.session:
        name = flask.session["name"]

    if not database.is_user(user_name):
        return jsonify({"count": 1, "actions": [Errors.gen_action(Errors.USER_NOT_FOUND)]})
    
    computer = comp_handler.get_computer(user_name, flask.request.remote_addr, create_new=True, name=name)
    computer.checked()

    parsed_answer = computer.parse_answer(data)

    if isinstance(parsed_answer, dict):
        parsed_answer = [parsed_answer]

    print(parsed_answer)

    return jsonify({"count": len(parsed_answer), "actions": parsed_answer})

if __name__ == "__main__":
    app.run(debug=DEBUG, port=PORT, host=HOST)
