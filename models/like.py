from google.appengine.ext import db
from models.user import User
from models.post import Post
from helper import *


class Like(db.Model):
    post = db.ReferenceProperty(Post, required=True)
    user = db.ReferenceProperty(User, required=True)
