from google.appengine.ext import db
import time
from models.user import User
from models.post import Post
from models.like import Like
from models.comment import Comment
from handlers.handler import Handler
from helper import *


class DeleteComment(Handler):
    def get(self, post_id, comment_id):
        if not self.user:
            self.render("/login")
            return
        
        # get the comment from the comment id
        comment = Comment.get_by_id(int(comment_id))
        # check if there is a comment associated with that id
        if comment:
            # check if this user is the author of this comment
            if comment.user.name == self.user.name:
                # delete the comment and redirect to the post page
                db.delete(comment)
                time.sleep(0.1)
                self.redirect('/post/%s' % str(post_id))
            # otherwise if this user is not the author of this comment throw an
            # error
            else:
                self.write("You cannot delete other user's comments")
        # otherwise if there is no comment associated with that id throw an
        # error
        else:
            self.write("This comment no longer exists")
