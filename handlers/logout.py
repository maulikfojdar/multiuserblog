from handlers.handler import Handler
from helper import *


class Logout(Handler):
    def get(self):
        self.logout()
        self.redirect('/')
