from flask import Flask, request, make_response, jsonify
import json
import random
import string


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

def random_str():
    res = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return res


@app.route("/send", methods=["POST"])
def send_msg():
    data = request.json
    chat_ids = data["chat_id"]
    username = data["username"]
    msg_type = data["msg_type"]
    msg_data = data["msg_data"]

    if not msg_validation(username, chat_ids, msg_type, msg_data):
        return make_response("error", 400)

    chat_id_list = chat_ids.split(",")

    db = load_js()
    for chat_id in chat_id_list:
        if not db.get(chat_id):
            db[chat_id] = {}
        msg_uuid = random_str()
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
    username = data["username"]

    if not msg_validation(chat_ids, username):
        return make_response("error", 400)

    chat_ids_list = chat_ids.split(",")
    db = load_js()

    # filtering data
    data = {}
    remove_msg_ids = []
    for chat_id in chat_ids_list:
        if not db.get(chat_id):
            continue

        for msg_id, msg_data in db[chat_id].items():
            if msg_data["username"] == username:
                continue
            if not data.get(chat_id):
                data[chat_id] = {}
            data[chat_id][msg_id] = msg_data
            remove_msg_ids.append(msg_id)

    for chat_id in chat_ids_list:
        if chat_id not in list(db.keys()):
            continue
        elif not db[chat_id]:
            db.pop(chat_id)

        for msg_id in remove_msg_ids:
            if not db[chat_id].get(msg_id):
                continue
            db[chat_id].pop(msg_id)

    save_js(db)
    return jsonify(data)


if __name__=="__main__":
    app.run()