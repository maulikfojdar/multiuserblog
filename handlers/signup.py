from handlers.handler import Handler
from models.user import User
from helper import *


class Signup(Handler):
    def get(self):
        self.render("signup.html")

    def post(self):
        have_error = False
        username = self.request.get("username")
        password = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")

        params = dict(username=username, email=email)

        if not valid_username(username):
            params['error_username'] = "That's not a valid username"
            have_error = True

        if not valid_password(password):
            params['error_password'] = "That's not a valid password"
            have_error = True
        elif password != verify:
            params['error_verify'] = "The passwords do not match!"
            have_error = True

        if have_error:
            self.render("signup.html", **params)
        else:
            u = User.by_name(username)
            if u:
                msg = 'That user already exists.'
                self.render('signup.html', error_username=msg)
            else:
                u = User.register(username, password, email)
                u.put()
                self.login(u)
                self.redirect('/')
