import secrets
import time


class Otp:
    def getotp(self):
        t = time.time()
        rand = 0
        while rand == 0:
            rand = secrets.randbelow(10000)
        return (rand, t)


if __name__ == "__main__":
    print(Otp.getotp())
