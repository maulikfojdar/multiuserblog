from google.appengine.ext import db
from handlers.handler import Handler
from helper import *


class MainPage(Handler):
    
    
    def get(self):
            posts = db.GqlQuery("SELECT * FROM Post ORDER BY created DESC")
            if posts:
                self.render("main.html", posts=posts)
