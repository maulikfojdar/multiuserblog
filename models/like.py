from google.appengine.ext import db
from models.user import User
from models.post import Post
from helper import *


class Like(db.Model):
    post = db.ReferenceProperty(Post, required=True)
    user = db.ReferenceProperty(User, required=True)
    
    # get number of likes for a blog id
    @classmethod
    def by_post_id(cls, post_id):
        l = Like.all().filter('post =', post_id)
        return l.count()
    
    # get number of likes for a blog and user id
    @classmethod
    def check_like(cls, post_id, user_id):
        cl = Like.all().filter('post =', \
                               post_id).filter('user =', user_id)
        return cl.count()
