from flask import Flask, request, make_response, jsonify
import json


app = Flask(__name__)
db_name = "mydb.json"

allowed_ids = []
disallowed_ids = []


def save_js(dic):
    try:
        with open(db_name, "wt") as json_file:
            json.dump(dic, json_file)
    except Exception:
        return False
    return True


def load_js():
    try:
        with open(db_name) as json_file:
            data = json.load(json_file)
    except Exception:
        data = {}
        with open(db_name, "wt") as json_file:
            json.dump(data, json_file)
    return data


def msg_validation(*args):
    for arg in args:
        if not arg:
            return False
    return True


@app.route("/send", methods=["POST"])
def send_msg():
    data = request.json
    chat_ids = data["chat_id"]
    username = data["username"]
    msg_type = data["msg_type"]
    msg_data = data["msg_data"]
    msg_uuid = data["msg_uuid"]

    if not msg_validation(username, chat_ids, msg_type, msg_data, msg_uuid):
        return make_response("error", 400)

    chat_id_list = chat_ids.split(",")

    db = load_js()
    for chat_id in chat_id_list:
        if not db.get(chat_id):
            db[chat_id] = {}

        db[chat_id][msg_uuid] = {
            "msg_type": msg_type,
            "msg_data": msg_data,
            "username": username
            }

    save_js(db)
    return make_response("ok", 200)


@app.route("/updates")
def get_msg():
    data = request.json
    chat_ids = data["chat_id"]

    if not msg_validation(chat_ids):
        return make_response("error", 400)

    chat_ids_list = chat_ids.split(",")
    db = load_js()

    # filtering data
    data = {}
    for chat_id in chat_ids_list:
        if not db.get(chat_id):
            continue
        data[chat_id] = db[chat_id]

    for chat_id in chat_ids_list:
        if db.get(chat_id):
            db.pop(chat_id)

    save_js(db)
    return jsonify(data)


if __name__=="__main__":
    app.run()