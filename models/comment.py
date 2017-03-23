from google.appengine.ext import db
from models.user import User
from models.post import Post
from helper import *


class Comment(db.Model):
    post = db.ReferenceProperty(Post, required=True)
    user = db.ReferenceProperty(User, required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    text = db.TextProperty(required=True)

    # get number of comments for a post
    @classmethod
    def count_by_post_id(cls, post):
        c = Comment.all().filter('post =', post)
        return c.count()

    # get all comments for a specific post
    @classmethod
    def all_by_post_id(cls, post):
        c = Comment.all().filter('post =', post).order('created')
        return c
