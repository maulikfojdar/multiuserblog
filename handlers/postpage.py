from google.appengine.ext import db
from models.user import User
from models.post import Post
from models.like import Like
from models.comment import Comment
from handlers.handler import Handler
from helper import *
import time


class PostPage(Handler):
    def get(self, post_id):
        post = db.get(db.Key.from_path("Post",
                                       int(post_id),
                                       parent=blog_key()))
        comments_count = Comment.count_by_post_id(post)
        post_comments = Comment.all_by_post_id(post)
        self.render("post.html",
                    post=post,
                    comments_count=comments_count,
                    post_comments=post_comments)
