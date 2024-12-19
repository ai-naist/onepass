"""main process"""
print("\rStandby.", end="")
import mylib
import time
import threading
import atexit


class Main:
    def __init__(self):
        mylib.sound.play("START")
        # Setting Times Limit and Timeout
        self.times_limit = 3
        self.limit_t_minutes = 1

        # Initial Check
        self.raspi = mylib.myraspi.Raspi(self.limit_t_minutes)
        self.raspi.pin_setup()
        atexit.register(self.raspi.clear_pin)
        self.raspi.initial_check()

        print("\rStandby..", end="")
        # Connect Google Sheet
        self.sheet = mylib.gsheet.Access("DenkiJikken")
        self.sheet.monitor_run()

        print("\rStandby...", end="")
        # smtp server
        self.sendmail = mylib.gmail.Mail()

        self.raspi.flow.join()
        print("\rStandby...OK!")

    def reset_value(self):
        self.status = ""
        self.input_pass = "0000"
        self.raspi.color_led("BLACK")
        # token[bool, 'token' or 'error_message']
        self.token = ""
        self.picts = []

    def reset_otp(self):
        # 0 fill -> 4 digits
        self.otp = mylib.otp.Otp()
        rand_t = self.otp.getotp()  # [secrets_number, start_time]
        self.rand = rand_t[0]
        self.start_time = rand_t[1]
        self.str_otp = str(self.rand).zfill(4)

    # Process Card Read and Google Sheet Collation
    def nfc_gsheet_getoken(self):
        status = False
        while not status:
            token = ""
            reader = mylib.nfcard.Card()
            while True:
                # Card Read Wait
                self.raspi.color_led("AMBER")  # Wait Signal
                reader.read()
                if (
                    reader.student_id != False
                ):  # Default = False    Type(student_id) = str
                    self.raspi.color_led("BLUE")  # Read Correctly
                    mylib.sound.play("READ")
                    break
                else:
                    self.raspi.color_led("MAGENTA")  # Read Error Signal
                    mylib.sound.play("ERROR")
                    time.sleep(1)

            # Get Matching Token
            token_list = self.sheet.getoken(int(reader.student_id))
            status = token_list[0]
            token = token_list[1]

            if status:
                self.token = token
                time.sleep(1)
                break
            else:
                print("Error:" + token)
                self.raspi.color_led("MAGENTA")
                mylib.sound.play("ERROR")
                sent_flag = self.sendmail.send(reader.student_id)
                time.sleep(1)
                if sent_flag:
                    self.raspi.color_led("CYAN")
                    mylib.sound.play("SENT")
                    time.sleep(2)

    def mkmessage(self):
        self.message = (
            "\nYour verification code is : "
            + self.str_otp
            + "\nThis code is valid for "
        )
        if self.limit_t_minutes == 1:
            self.message += "{} minute".format(self.limit_t_minutes)
        else:
            self.message += "{} minutes".format(self.limit_t_minutes)

    def run(self):
        try:
            while True:
                # Variable Initialization
                self.reset_value()

                self.nfc_gsheet_getoken()

                self.reset_otp()
                self.mkmessage()

                send = mylib.sendline.LineNotify()
                send.sendotp(self.token, self.message)

                self.picts.append(mylib.mycam.getcap())

                print("Please enter the verification code.")
                for i in range(self.times_limit):
                    self.input_pass = self.raspi.click_run(
                        self.input_pass, self.start_time
                    )

                    if self.input_pass == self.str_otp:
                        self.status = "Success"
                        print(self.status)
                        self.raspi.color_led("GREEN")
                        mylib.sound.play("COMPLETED")
                        self.sheet.logging(
                            [self.status, str(time.time() - self.start_time)]
                        )
                        # send.rmpicts(self.picts)
                        time.sleep(3)
                        break
                    elif time.time() - self.start_time < self.limit_t_minutes * 60:
                        if i < 2:
                            self.raspi.color_led("MAGENTA")
                            mylib.sound.play("ERROR")
                            self.picts.append(mylib.mycam.getcap())
                            print("Try again")
                            print("{} times left".format(self.times_limit - (i + 1)))
                            time.sleep(1)
                        else:
                            self.raspi.color_led("RED")
                            mylib.sound.play("FAILED")
                            self.picts.append(mylib.mycam.getcap())
                            self.status = "Failure"
                            print(self.status)
                            send.sendcam(self.token, self.picts)
                            self.sheet.logging(
                                [
                                    self.status,
                                    "Wrong {} times".format(self.times_limit),
                                ]
                            )
                            time.sleep(3)
                            break
                    else:
                        self.raspi.color_led("RED")
                        mylib.sound.play("FAILED")
                        print("The verification code has expired due to timeout.")
                        send.sendcam(self.token, self.picts)
                        self.sheet.logging(["Failure", "Timeout"])
                        time.sleep(3)
                        break

                # Remove Picture
                send.rmpicts(self.picts)

                # Monitor All Active Threads
                print(threading.enumerate())
                time.sleep(1)
        finally:
            self.raspi.clear_pin()
            self.sendmail.server.quit()


# Further processing is only performed if this code is called directly as a script.
if __name__ == "__main__":
    while True:
        try:
            main = Main()
            main.run()
        except Exception as err:
            print("Error:%s" % err)
