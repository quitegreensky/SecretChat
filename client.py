import requests
import string
import random
import json
from libs.encryption import Cipher
import threading
import time
from colorama import init
from colorama import Fore, Back, Style
init()

url = "http://127.0.0.1:5000"
db_name = "mydb_client.json"
chat_ids = "1"


class Messanger():

    def __init__(self, db_name, url, chat_ids) -> None:
        self.db_name = db_name
        self.url = url
        self.secret = "secret".encode("utf-8")
        self.chat_ids = chat_ids

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
                recv_data = cipher_obj.decrypt(bytes(msg_data, "utf-8"))
                self.log(f"{Back.GREEN}{chat_id}: {recv_data}")
            else:
                pass

    def update_message(self):
        t = threading.Thread(target=self._update_message)
        t.start()

    def _update_message(self, *args):
        while True:
            data = {
                "chat_id": self.chat_ids,
            }
            res = requests.get(url+"/updates", json=data)
            if not res.ok:
                self.log(Back.RED+"Unable to get updates")
                continue

            res_data = res.json()
            db = self.load_js()

            for res_chat_id, chat_data in res_data.items():
                if not db.get(res_chat_id):
                    db[res_chat_id] = {}
                db[res_chat_id].update(chat_data)
                self.new_message_handler(res_chat_id, chat_data)
            self.save_js(db)
            time.sleep(3)

    def send_message(self, data, path=None):
        cipher_obj = Cipher(self.secret)
        if data["msg_type"]=="txt":
            _data = data["msg_data"]
        else:
            pass

        data["msg_data"] = cipher_obj.encrypt(_data).decode("utf-8")

        data["msg_uuid"] = self.random_str()
        res = requests.post(url+"/send", json=data)
        if not res.ok:
            self.log("failed to send msg")
            return False
        self.log(f"{Fore.GREEN}Sent")
        return True

app = Messanger(db_name, url, chat_ids)

data = {
    "chat_id": "1",
    "chat_secret": "secret",
    "msg_type": "txt",
    "msg_data": "hello"
}
app.send_message(data, "image.png")
app.update_message()