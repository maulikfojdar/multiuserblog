from google.appengine.ext import db
from models.user import User
from models.post import Post
from models.like import Like
from models.comment import Comment
from handlers.handler import Handler
from helper import *
import time


class AddComment(Handler):
    def get(self, post_id, user_id):
        if not self.user:
            self.render('/login')
        else:
            self.render("addcomment.html")

    def post(self, post_id, user_id):
        if not self.user:
            self.render('/login')

        comment_text = self.request.get("comment_text")
        # check if there is anything entered in the comment text area
        if comment_text:
            # add comment to the comments database and refresh page
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            c = Comment(post=key,
                        user=self.user,
                        text=comment_text)
            c.put()
            time.sleep(0.1)
            self.redirect('/post/'+post_id)
        # otherwise if nothing has been entered in the text area throw
        # an error
        else:
            comment_error = "Please enter a comment\
                                in the text area to post"
            self.render("post.html",
                        comment_error=comment_error)
