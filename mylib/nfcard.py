"""nfc control"""
import nfc
import time


class Card:
    def __init__(self):
        self.student_id = False
        self.flag = False

    def rflag(self):
        time.sleep(0.1)
        return self.flag

    def refer(self, tag):
        service_code = 0x010B
        try:
            if isinstance(tag, nfc.tag.tt3.Type3Tag):
                try:
                    svcd = nfc.tag.tt3.ServiceCode(
                        service_code >> 6, service_code & 0x3F
                    )
                    blcd = nfc.tag.tt3.BlockCode(0, service=0)
                    block_data = tag.read_without_encryption([svcd], [blcd])
                    self.student_id = str(block_data[0:10].decode("utf-8"))
                except Exception as e:
                    print("Error:%s" % e)
                    self.student_id = False

            else:
                print("Error:tag isn't Type3Tag")
                print("Try again.")
                self.student_id = False
        except AttributeError as e:
            print("Error:%s" % e)
            self.student_id = False

        self.flag = True

    def read(self):
        print("Please touch your card.")
        with nfc.ContactlessFrontend("usb") as clf:
            clf.connect(rdwr={"on-connect": self.refer}, terminate=self.rflag)
            self.flag = False
        time.sleep(0.01)


if __name__ == "__main__":
    reader = Card()
    flag = True
    while flag:
        while True:
            reader.read()
            if reader.student_id != False:
                # flag=False
                time.sleep(1)
                break
            time.sleep(1)
        print(int(reader.student_id))
