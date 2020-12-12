from threading import Thread
from time import sleep, localtime
from numpy.random import randint

TOKEN_N = 128
CHARS = [chr(x) for x in list(range(48, 58)) + list(range(65, 91)) + list(range(97, 123))]

class UserHandler:
    def __init__(self, users, users_global, disconnect_func):
        self.users = users_global
        self.init_users(users)
        self.disconnect_func = disconnect_func
        self.cln_thr = Thread(target=self.user_cleaner)
        self.cln_thr.start()

    def init_users(self, users):
        for user in users:
            tok = self.tokenize_user(user)
            self.users[tok]['cam'] = 'CAM1'
            self.users[tok]['last_seen'] = None

    def tokenize_user(self, user):
        try:
            prev_token = [self.users[tok]['name'] for tok in self.users].index(user['name'])
            del self.users[prev_token]
        except:
            pass
        new_token = self.gen_new_token()
        self.users[new_token] = user
        return new_token

    def user_cleaner(self):
        while True:
            now = localtime()
            for user in self.users.values():
                if user['last_seen'] is not None:
                    total_sec = (user['last_seen'].tm_hour - now.tm_hour) * 3600 + \
                                    (user['last_seen'].tm_min - now.tm_min) * 60 + \
                                    (user['last_seen'].tm_sec - now.tm_sec)
                    if total_sec > 60:
                        self.disconnect_func(user['cam'])
            sleep(60)

    @staticmethod
    def gen_new_token():
        return ''.join([CHARS[x] for x in randint(0, len(CHARS), TOKEN_N)])
