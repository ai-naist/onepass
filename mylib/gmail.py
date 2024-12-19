import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Mail:
    def __init__(self):
        self.legacy_id = ""
        smtp_server = "smtp.gmail.com"
        port = 587
        self.server = smtplib.SMTP(smtp_server, port)
        self.server.starttls()
        self.login_address = "jikken2022ak@gmail.com"
        login_password = "XXX"
        self.server.login(self.login_address, login_password)

    def send(self, student_id):
        if self.legacy_id != student_id:
            message = MIMEMultipart()
            message[
                "Subject"
            ] = "Get an access token for LINE Notify and register it in the management system"
            message["From"] = self.login_address

            message["To"] = "seb{}@st.osakafu-u.ac.jp".format(student_id[-5:])
            text = MIMEText(
                "\nAccess the Google forms from the URL below."
                + "\nObtain a LINE Notify access token, and register it in the management system."
                + "\n\nURL: https://docs.google.com/forms/d/e/1FAIpQLSfzJJJrDRkWLtnyGqn3S2NgJKigaoNADGdNMGaiturHKMbKUQ/viewform?usp=sf_link"
                + "\n\n\nIf you received this message in error, simply delete it."
            )
            message.attach(text)
            self.server.send_message(message)
            self.legacy_id = student_id
            print("mail has sent")
            print("To: " + message["To"])
            return True

        else:
            print("alredy sent")
            return False


if __name__ == "__main__":
    import time

    t = time.time()
    s = Mail()
    print(time.time() - t)
    t = time.time()
    s.send("1201201010")
    print(time.time() - t)
    # s.server.quit()
    print(time.time() - t)
