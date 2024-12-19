"""Google Sheet control"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import threading
import datetime
from . import sendline

# Google Sheet URL:
# https://drive.google.com/drive/u/9/folders/1L8HHCnWtYgGrn-xUKqW78i4ghqj5GhVt


class Access:
    def __init__(self, f_name):
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        path = "mylib/json/jikken.json"  # jikken.json path
        cred = ServiceAccountCredentials.from_json_keyfile_name(path, scope)
        self.gc = gspread.authorize(cred)
        sh = self.gc.open(f_name)
        self.form_wks = sh.worksheet("sheet_form")
        self.log_wks = sh.worksheet("sheet_log")

    def monitor_run(self):
        # Monitoring Thred
        monitor = threading.Thread(target=self.monitoring)
        monitor.start()

    def logging(self, status):
        new_log = [
            str(datetime.datetime.now()),
            str(self.student_dict[0]["FIRST"])
            + " "
            + str(self.student_dict[0]["LAST"]),
            status[0],
            status[1],
        ]
        self.log_wks.append_row(new_log)

    def getoken(self, student_id):
        # get list of dictionaries from wks
        key_list = self.form_wks.get_all_records(
            empty2zero=False, head=1, default_blank=""
        )
        # get dictionary of matching id from key_list
        self.student_dict = list(
            filter(lambda item: item["STUDENT_ID"] == student_id, key_list)
        )
        if self.student_dict == []:
            return [False, "Your student ID number is not registered."]
        elif self.student_dict[0]["KEY"] == "":
            return [False, "Your token registration could not be verified."]
        else:
            token = self.student_dict[0]["KEY"]
            return [True, token]

    def monitoring(self):
        # Initialization
        old_key_list = self.form_wks.get_all_records(
            empty2zero=False, head=1, default_blank=""
        )

        while True:
            try:
                # get list of dictionaries from wks
                key_list = self.form_wks.get_all_records(
                    empty2zero=False, head=1, default_blank=""
                )

                if old_key_list != key_list:
                    if len(old_key_list) == len(key_list):
                        for i in range(len(key_list)):
                            # Extract Difference
                            difference_dict = dict(
                                key_list[i].items() - old_key_list[i].items()
                            )

                        if difference_dict != {}:
                            print(
                                "\r"
                                + str(key_list[i]["DATE"])
                                + ","
                                + str(key_list[i]["FIRST"])
                                + " "
                                + str(key_list[i]["LAST"])
                            )

                            token = key_list[i]["KEY"]
                            send = sendline.LineNotify()
                            send.sendreginotify(token)

                    else:
                        i = len(key_list) - 1
                        difference_dict = dict(key_list[i])
                        print(
                            "\r"
                            + str(key_list[i]["DATE"])
                            + ","
                            + str(key_list[i]["FIRST"])
                            + " "
                            + str(key_list[i]["LAST"])
                        )
                        token = key_list[i]["KEY"]
                        send = sendline.LineNotify()
                        send.sendreginotify(token)

                old_key_list = key_list
                time.sleep(1)

            except Exception as err:
                print("Error:%s" % err)


if __name__ == "__main__":
    instance = Access()
