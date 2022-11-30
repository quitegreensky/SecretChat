__version__ = "1.1.0"
__appname__ = "SecretChat"
__author__ = "quitegreensky"

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
import os
import random
import platform
import subprocess

init()

configs = "configs.json"


class Cipher:
    def __init__(self, key, **kw):
        os.environ["t_stop"] = "0"
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

    def __init__(self, configs) -> None:
        self.configs = self.load_js(configs)

        interval = self.configs.get("interval")
        if not interval:
            interval = 3
        self.interval = interval

        username = self.configs.get("username")
        if not username:
            username = "User"+str(random.randint(1,100))
        self.username = username

        count = self.configs.get("count")
        if not count:
            count = 10
        self.count = count

        self.timeout = 10
        self.invalid_secret_warning = self.configs.get("invalid_secret_warning")
        self.url = self.configs["url"]
        self.chat_id = self.configs["chat_id"]
        self.secret = None
        self._handled_msg = []
        self.t = None
        os.environ["t_stop"] = "0"

    def end_app(self):
        self.log(f"Ending app...")
        os.environ["t_stop"] = "1"
        if self.t:
            self.t.join()
        exit()

    def set_secret(self, secret):
        self.secret = secret.encode("utf-8")

    def save_js(self, dic, path = None):
        try:
            with open(path, "wt") as json_file:
                json.dump(dic, json_file)
        except Exception:
            return False
        return True

    def load_js(self, path = None):
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
        if username==self.username:
            color = Back.GREEN
        else:
            color = Back.BLUE

        recv_data = self.decode_message(msg_data, msg_type)

        if not recv_data:
            return
        if recv_data:
            self.log(f"{color}{username}: {recv_data}")

    def update_message(self):
        self.t = threading.Thread(target=self._update_message)
        self.t.start()

    def test_connection(self):
        self.log(f"{Back.CYAN}Testing connection to {self.url}")
        url = self.url

        param = '-n' if platform.system().lower()=='windows' else '-c'
        url = url.replace("http://", "")
        url = url.replace("https://", "")
        command = ['ping', param, '2', url]
        connection_res = subprocess.call(command) ==0

        res = requests.get(self.url+"/version", timeout=self.timeout)
        if not res.ok or not connection_res:
            self.log(f"{Back.RED}Connection error {url}")
            if connection_res and not res.ok:
                self.log(f"{Back.RED}Server responds but it's not installed correctly")
            return False

        versoin = res.text
        if versoin!=__version__:
            self.log(f"{Back.YELLOW}Warning: The server is using a different version: {versoin}")

        self.log(f"{Back.GREEN}Connection established {url}")
        return True

    def _update_message(self, *args):
        while True:
            if os.environ["t_stop"] == "1":
                return
            data = {
                "chat_id": self.chat_id,
                "count": self.count
            }
            res = requests.get(self.url+"/updates", json=data , timeout=self.timeout)
            if not res.ok:
                self.log(Back.RED+"Unable to get updates")
                time.sleep(self.interval)
                continue

            res_data = res.json()[self.chat_id][::-1]
            for chat_data in res_data:
                msg_uuid = chat_data["msg_uuid"]
                if msg_uuid in self._handled_msg:
                    continue
                self._handled_msg.append(msg_uuid)
                self.new_message_handler(msg_uuid, chat_data)
            time.sleep(self.interval)

    def send_message(self, data, path=None):
        data["username"] = self.username
        data["chat_id"] = self.chat_id

        cipher_obj = Cipher(self.secret)
        if data["msg_type"]=="txt":
            _data = data["msg_data"]
        else:
            pass

        data["msg_data"] = cipher_obj.encrypt(_data).decode("utf-8")
        res = requests.post(self.url+"/send", json=data, timeout=self.timeout)
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
                recv_data = None
        else:
            pass
        if not recv_data and self.invalid_secret_warning:
            self.log(f"{Back.RED}Invalid Secret")
        return recv_data

def main():
    app = Messanger(configs)
    app.log(f"{Back.CYAN}{__appname__} by {__author__} version {__version__}")
    if not app.test_connection():
        input(f"Press enter key to exit...")
        app.end_app()

    secret = getpass.getpass(f"{Fore.RED}Enter your secret:{Fore.RESET}")
    app.log(f"{Fore.CYAN}Conversation started...\n=====================")
    if not secret:
        app.log(f"{Fore.RED}Secret cannot be empty")
        input(f"Press enter key to exit...")
        app.end_app()

    app.set_secret(secret)
    app.update_message()

    while True:
        input_data = input("")
        if len(input_data)==0:
            continue

        if input_data=="--help":
            continue

        if input_data=="--end":
            app.end_app()

        data = {
            "msg_type": "txt",
            "msg_data": input_data
        }
        app.send_message(data)

if __name__=="__main__":
    main()