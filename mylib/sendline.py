"""sending line notify"""
import requests
import fileinput
import os
from . import mycam


class LineNotify:
    def __init__(self):
        self.url = "https://notify-api.line.me/api/notify"

    def set(self):
        self.head = {"Authorization": "Bearer " + self.token}
        self.load = {"message": self.message}

    def sendotp(self, token, message):
        self.token = token
        self.message = message
        self.set()
        r = requests.post(self.url, headers=self.head, params=self.load)
        print("A verification code has been sent to LINE.")

    def sendcam(self, token, path):
        self.token = token
        self.message = "\nSomeone may have tried to circumvent authentication by impersonating you."
        self.set()
        r = requests.post(self.url, headers=self.head, params=self.load)
        self.load = {"message": "Warning!"}
        for i in path:
            files = {"imageFile": open(i, "rb")}
            r = requests.post(
                self.url, headers=self.head, params=self.load, files=files
            )

    def rmpicts(self, path):
        if path:  # [] --> False
            for i in path:
                os.remove(i)
        else:
            pass

    def sendreginotify(self, token):
        self.token = token
        self.message = "Your submission has been registered."
        self.set()
        r = requests.post(self.url, headers=self.head, params=self.load)


if __name__ == "__main__":
    token = "c6DCxtna6VRPIX6oUOtJk4GW2XquwXuBomp7Cqsypsi"
    instance = LineNotify()
    # instance.sendotp(token,'hi')
    instance.sendcam(token)
