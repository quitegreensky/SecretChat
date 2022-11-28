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
configs = "configs.json"

class Messanger():

    def __init__(self, db_name, url, chat_ids, configs) -> None:
        self.db_name = db_name
        self.url = url
        self.secret = "secret".encode("utf-8")
        self.chat_ids = chat_ids
        self.configs = self.load_js(configs)

    def save_js(self, dic, path = None):
        if not path:
            path = self.db_name
        try:
            with open(path, "wt") as json_file:
                json.dump(dic, json_file)
        except Exception:
            return False
        return True

    def load_js(self, path = None):
        if not path:
            path = self.db_name
        try:
            with open(path) as json_file:
                data = json.load(json_file)
        except Exception:
            data = {}
            with open(path, "wt") as json_file:
                json.dump(data, json_file)
        return data

    def log(self, txt):
        print(txt+Style.RESET_ALL)

    @staticmethod
    def random_str():
        res = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return res

    def new_message_handler(self, chat_id, chat_data):
        for _uuid, msg in chat_data.items():
            msg_data = msg["msg_data"]
            msg_type = msg["msg_type"]
            username = msg["username"]
            recv_data = self.decode_message(msg_data, msg_type)
            if recv_data:
                self.log(f"{Back.GREEN}{username}: {recv_data}")

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
        print(self.configs)
        data["username"] = self.configs["username"]
        data["chat_id"] = self.configs["chat_id"]
        data["chat_secret"] = self.configs["chat_secret"]

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

    def decode_message(self, msg_data, msg_type):
        cipher_obj = Cipher(self.secret)
        if msg_type=="txt":
            recv_data = cipher_obj.decrypt(bytes(msg_data, "utf-8"))
        else:
            pass
        return recv_data

    def show_history(self, count):
        db = self.load_js()
        _count = 0
        for chat_id, chat_data in list(db.items()):
            for msg_id, mydata in list(reversed(list(chat_data.items()))):
                msg_data = mydata["msg_data"]
                msg_type = mydata["msg_type"]
                username = mydata["username"]
                recv_data = self.decode_message(msg_data, msg_type)
                if recv_data:
                    self.log(f"{Back.GREEN}{username}: {recv_data}")
                    count+=1
                if _count>=count:
                    return


app = Messanger(db_name, url, chat_ids, configs)
app.update_message()

while True:
    input_data = input(Fore.CYAN)
    if len(input_data)==0:
        continue

    if input_data=="--help":
        continue

    if "--history" in input_data:
        count = input_data.replace("--history", "").replace(" ","")
        try:
            app.show_history(int(count))
        except:
            app.log(Fore.RED+"Invalid parameter")
        continue

    data = {
        "msg_type": "txt",
        "msg_data": input_data
    }
    app.send_message(data)