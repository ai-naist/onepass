from picamera import PiCamera
import datetime


def getcap():
    with PiCamera(resolution=(1280, 720)) as cam:
        now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        # path = '/home/pi/Downloads/Picam001.jpg'
        path = "/home/pi/pi/onepass/cam/image{}.jpg".format(now)
        cam.capture(path)
    return path


if __name__ == "__main__":
    getcap()
