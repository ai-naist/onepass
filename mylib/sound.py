from time import sleep
import subprocess

file_dict = {
    "START": "startup",
    18: "s_button",
    15: "o_button",
    "ERROR": "error",
    "FAILED": "criticalstop",
    "READ": "read_success",
    "COMPLETED": "unlock",
    "SENT": "sent",
}


def play(command):
    order = [
        "mpg321",
        "/home/pi/pi/onepass/audio/{}.mp3".format(file_dict[command]),
    ]
    process = subprocess.Popen(order)
    sleep(0.01)


# Further processing is only performed if this code is called directly as a script.
if __name__ == "__main__":
    for a in file_dict:
        play(a)
        sleep(1)
