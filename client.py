import requests
import json
import threading
import time
from colorama import init
from colorama import Fore, Back, Style
import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES
import getpass

init()

db_name = "mydb_client.json"
configs = "configs.json"


class Cipher:
    def __init__(self, key, **kw):
        self.bs = AES.block_size
        self.key = hashlib.sha256(key.decode("utf-8").encode()).digest()

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode()))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[: AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size :])).decode(
            "utf-8"
        )

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(
            self.bs - len(s) % self.bs
        )

    @staticmethod
    def _unpad(s):
        return s[: -ord(s[len(s) - 1 :])]


class Messanger():

    def __init__(self, db_name, configs) -> None:
        self.db_name = db_name
        self.configs = self.load_js(configs)
        self.url = self.configs["url"]
        self.chat_id = self.configs["chat_id"]
        self.secret = None
        self.handled_msg = []

    def set_secret(self, secret):
        self.secret = secret.encode("utf-8")

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
        print(txt+Style.RESET_ALL+Fore.RESET+Back.RESET)

    def new_message_handler(self, chat_id, chat_data):
        msg_data = chat_data["msg_data"]
        msg_type = chat_data["msg_type"]
        username = chat_data["username"]
        color = None
        if username==self.configs["username"]:
            color = Back.GREEN
        else:
            color = Back.BLUE
        recv_data = self.decode_message(msg_data, msg_type)
        if not recv_data:
            return
        if recv_data:
            self.log(f"{color}{username}: {recv_data}")

    def update_message(self):
        t = threading.Thread(target=self._update_message)
        t.start()
        return t

    def _update_message(self, *args):
        while True:
            if t_stop:
                return
            data = {
                "chat_id": self.chat_id,
                "count": self.configs["count"]
            }
            res = requests.get(self.url+"/updates", json=data)
            if not res.ok:
                self.log(Back.RED+"Unable to get updates")
                time.sleep(3)
                continue

            res_data = res.json()[self.chat_id][::-1]
            for chat_data in res_data:
                msg_uuid = chat_data["msg_uuid"]
                if msg_uuid in self.handled_msg:
                    continue
                self.handled_msg.append(msg_uuid)
                self.new_message_handler(msg_uuid, chat_data)
            time.sleep(3)

    def send_message(self, data, path=None):
        data["username"] = self.configs["username"]
        data["chat_id"] = self.configs["chat_id"]

        cipher_obj = Cipher(self.secret)
        if data["msg_type"]=="txt":
            _data = data["msg_data"]
        else:
            pass

        data["msg_data"] = cipher_obj.encrypt(_data).decode("utf-8")
        res = requests.post(self.url+"/send", json=data)
        if not res.ok:
            self.log("failed to send msg")
            return False
        self.log(f"{Fore.GREEN}Sent")
        return True

    def decode_message(self, msg_data, msg_type):
        cipher_obj = Cipher(self.secret)
        if msg_type=="txt":
            try:
                recv_data = cipher_obj.decrypt(bytes(msg_data, "utf-8"))
            except:
                self.log(f"{Back.RED}Invalid Secret")
                return False
        else:
            pass
        return recv_data


app = Messanger(db_name, configs)
app.log(f"{Fore.RED}\nConverstation initiated.\n=====================")
secret = getpass.getpass(f"{Fore.RED}Enter your secret:{Fore.RESET}")
app.set_secret(secret)

t_stop = False
t = app.update_message()

while True:
    input_data = input("")
    if len(input_data)==0:
        continue

    if input_data=="--help":
        continue

    if input_data=="--end":
        t_stop = True
        t.join()
        exit()

    data = {
        "msg_type": "txt",
        "msg_data": input_data
    }
    app.send_message(data)