from threading import Thread
from time import sleep, localtime
from numpy.random import randint

TOKEN_N = 128
CHARS = [chr(x) for x in list(range(48, 58)) + list(range(65, 91)) + list(range(97, 123))]

class UserHandler:
    def __init__(self, users, users_global):
        self.users = users_global
        self.init_users(users)

    def init_users(self, users):
        for user in users:
            self.tokenize_user(user)

    def retokenize(self, token):
        new_token = self.gen_new_token()
        self.users[new_token] = self.users[token]
        del self.users[token]
        return new_token

    def tokenize_user(self, user):
        try:
            prev_token = [self.users[tok]['name'] for tok in self.users].index(user['name'])
            del self.users[prev_token]
        except:
            pass
        new_token = self.gen_new_token()
        self.users[new_token] = user
        return new_token

    def tokenize_all_users(self):
        for token in self.users:
            self.retokenize(token)
        return self.users


    @staticmethod
    def gen_new_token():
        return ''.join([CHARS[x] for x in randint(0, len(CHARS), TOKEN_N)])
