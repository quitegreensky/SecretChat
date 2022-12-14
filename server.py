__version__ = "1.1.0"

from flask import Flask, request, make_response, jsonify
import json
import datetime

app = Flask(__name__)
db_name = "mydb.json"

MAX_REPLAYS_COUNT = 20 # Max amount of history to replay


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


def timestamp():
    dt = datetime.datetime.now(datetime.timezone.utc)
    utc_time = dt.replace(tzinfo=datetime.timezone.utc)
    utc_timestamp = utc_time.timestamp()
    return utc_timestamp


@app.route("/version")
def version():
    return __version__


@app.route("/send", methods=["POST"])
def send_msg():
    data = request.json
    chat_id = data["chat_id"]
    username = data["username"]
    msg_type = data["msg_type"]
    msg_data = data["msg_data"]

    if not msg_validation(username, chat_id, msg_type, msg_data):
        return make_response("error", 400)

    db = load_js()
    if not db.get(chat_id):
        db[chat_id] = []

    _ts = str(timestamp())
    db[chat_id].append({
        "msg_uuid": _ts,
        "msg_type": msg_type,
        "msg_data": msg_data,
        "username": username,
        "timestamp": _ts
    })

    save_js(db)
    return make_response("ok", 200)


@app.route("/updates")
def get_msg():
    data = request.json
    chat_id = data["chat_id"]
    count = data["count"]

    if not msg_validation(chat_id, count):
        return make_response("error", 400)

    try:
        count = int(count)
    except:
        return make_response("error", 400)

    db = load_js()

    data = {}
    if not db.get(chat_id):
        return jsonify({chat_id:[]})

    _count = 0
    for msg_data in db[chat_id][::-1]:
        if not data.get(chat_id):
            data[chat_id] = []
        data[chat_id].append(msg_data)
        _count+=1
        if _count>MAX_REPLAYS_COUNT and MAX_REPLAYS_COUNT!=0:
            break;

    save_js(db)
    return jsonify(data)


if __name__=="__main__":
    app.run()