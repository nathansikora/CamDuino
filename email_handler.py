import smtplib
from time import localtime, sleep
from threading import Thread
from email.mime.text import MIMEText
from json import load

with open('settings.json', 'r') as ff:
    dd = load(ff)['email_handler']
    USERNAME = dd['USERNAME']
    PASS = dd['PASS']

USERNAME = 'servercamduino@gmail.com'
PASS = 'SqJXimEihbDQtHzLiLLQJSnOWoObfqROzAWXjsxmnuVlJbJvwWNbgDlZ7geG8np'
PORT = 587
SEND_HOUR = 6


class EmailHandler:
    def __init__(self, users, out_site, username=USERNAME, password=PASS):
        self.users = users
        self.out_site = out_site
        self.username = username
        self.password = password
        self.is_sent_today = False

        self.mail_thr = Thread(target=self.check_hour_for_send)
        self.mail_thr.start()

    def send_tokens_via_email(self):
        # Create a secure SSL context
        server = smtplib.SMTP('smtp.gmail.com:{0}'.format(PORT))
        server.ehlo()
        server.starttls()
        server.login(self.username, self.password)

        for token in self.users:
            msg = MIMEText(u'<a href="{0}">click here</a>'.format(self.out_site[0] + token), 'html')
            msg['Subject'] = 'daily camduino link for {0}'.format(self.users[token]['name'])

            server.sendmail(msg=msg.as_string(), from_addr=self.username, to_addrs=self.users[token]['email'])
        server.close()

    def check_hour_for_send(self):
        while True:
            cur_hour = localtime().tm_hour
            if cur_hour >= SEND_HOUR:
                if self.is_sent_today is False:
                    self.send_tokens_via_email()
                    self.is_sent_today = True
            else:   # cur_hour < SEND_HOUR
                self.is_sent_today = False
            sleep(3600)
