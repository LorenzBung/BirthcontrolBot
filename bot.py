import requests
import json
import configparser as cfg


class telegram_chatbot():

    def __init__(self):
        self.token = "your_telegram_token"
        self.base = "https://api.telegram.org/bot{}/".format(self.token)
        self.status = {}
        self.time = {}
        self.reminder = {}

    def get_updates(self, offset=None):
        url = self.base + "getUpdates?timeout=100"
        if offset:
            url = url + "&offset={}".format(offset + 1)
        r = requests.get(url)
        return r.json()

    def send_message(self, msg, chat_id):
        url = self.base + "sendMessage?chat_id={}&text={}".format(chat_id, msg)
        if msg is not None:
            requests.get(url)
