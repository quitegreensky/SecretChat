import requests
import string
import random
import json
from libs.encryption import Cipher

url = "http://127.0.0.1:5000"
db_name = "mydb_client.json"


class Messanger():

    def __init__(self, db_name, url) -> None:
        self.db_name = db_name
        self.url = url
        self.secret = "secret".encode("utf-8")

    def save_js(self, dic):
        try:
            with open(self.db_name, "wt") as json_file:
                json.dump(dic, json_file)
        except Exception:
            return False
        return True

    def load_js(self):
        try:
            with open(self.db_name) as json_file:
                data = json.load(json_file)
        except Exception:
            data = {}
            with open(self.db_name, "wt") as json_file:
                json.dump(data, json_file)
        return data

    def log(self, txt):
        print(txt)

    @staticmethod
    def random_str():
        res = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return res

    def new_message_handler(self, chat_id, chat_data):
        for _uuid, msg in chat_data.items():
            cipher_obj = Cipher(self.secret)
            msg_data = msg["msg_data"]
            msg_type = msg["msg_type"]
            if msg_type=="txt":
                self.log( cipher_obj.decrypt(bytes(msg_data, "utf-8")) )
            else:
                fname = f"{self.random_str()}.{msg_type}"
                with open(fname, "wb") as f:
                    f.write( bytes(cipher_obj.decrypt(msg_data)) )

    def update_message(self, chat_id):
        data = {
            "chat_id": chat_id,
        }
        res = requests.get(url+"/updates", json=data)
        if not res.ok:
            self.log("unable to get updates")
            return False

        res_data = res.json()
        db = self.load_js()

        for res_chat_id, chat_data in res_data.items():
            if not db.get(res_chat_id):
                db[res_chat_id] = {}
            db[res_chat_id].update(chat_data)
            self.new_message_handler(res_chat_id, chat_data)
        self.save_js(db)

    def send_message(self, data, path=None):
        cipher_obj = Cipher(self.secret)
        if data["msg_type"]=="txt":
            _data = data["msg_data"]
        else:
            _data = None
            with open(path, "rb") as f:
                _data =  str(f.read())[1:].replace("'","")

        data["msg_data"] = cipher_obj.encrypt(_data).decode("utf-8")

        data["msg_uuid"] = self.random_str()
        res = requests.post(url+"/send", json=data)
        if not res.ok:
            self.log("failed to send msg")
            return False
        self.log("sent")
        return True


app = Messanger(db_name, url)


data = {
    "chat_id": "1",
    "chat_secret": "secret",
    "msg_type": "png",
    "msg_data": "hello"
}
app.send_message(data, "image.png")
app.update_message("1")