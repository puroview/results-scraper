import datetime
import http.client
import os
import smtplib
import time
import urllib
from email.message import EmailMessage


class Notifier():
    def __init__(self):
        pass
        #self.emailkeys = emailkeys
        #self.pushkeys = pushkeys

    def email(self):
        emailBody = EmailMessage()
        with open(self.wfile_name, 'r') as wf:
            emailBody.set_content(wf.read())
            wf.close()
        emailBody['Subject'] = "Winning {} Postcodes for {}".format(
            self.draw.capitalize(), datetime.date.today())

        smtpObj = smtplib.SMTP(self.emailkeys["srv"], self.emailkeys["port"])
        smtpObj.ehlo()
        smtpObj.starttls()
        smtpObj.login(self.emailkeys["login"], self.emailkeys["password"])
        smtpObj.sendmail(
            self.emailkeys["fromaddr"], self.emailkeys["toaddr"], emailBody.as_string())
        smtpObj.quit()

    def pushover(self, message):
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
                     urllib.parse.urlencode({
                         "token": "a313kfvi8omf12fc1r1xsj9u5qxij5",
                         "user": "VP9MGj3hhrqkOBieKVfB8cKNexboMk",
                         "message": (message)
                         }),
                     {"Content-type": "application/x-www-form-urlencoded"})
        conn.getresponse()
