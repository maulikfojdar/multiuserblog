from google.appengine.ext import db
import time

# Models
from models.user import User
from models.post import Post
from models.like import Like
from models.comment import Comment
from handlers.handler import Handler
from helper import *


class EditComment(Handler):
    def get(self, post_id, comment_id):
        # get the blog and comment from blog id and comment id
        post = Post.get_by_id(int(post_id), parent=blog_key())
        comment = Comment.get_by_id(int(comment_id))
        # check if there is a comment associated with that id
        if comment:
            # check if this user is the author of this comment
            if comment.user.name == self.user.name:
                # take the user to the edit comment page and load the content
                # of the comment
                self.render("editcomment.html", comment_text=comment.text)
            # otherwise if this user is the author of this comment throw and
            # error
            else:
                error = "You cannot edit other users' comments'"
                self.render("editcomment.html", edit_error=error)
        # otherwise if there is no comment associated with that ID throw an
        # error
        else:
            error = "This comment no longer exists"
            self.render("editcomment.html", edit_error=error)

    def post(self, post_id, comment_id):
        # if the user clicks on update comment
        if self.request.get("update_comment"):
            # get the comment for that comment id
            comment = Comment.get_by_id(int(comment_id))
            # check if this user is the author of this comment
            if comment.user.name == self.user.name:
                # update the text of the comment and redirect to the post page
                comment.text = self.request.get('comment_text')
                comment.put()
                time.sleep(0.1)
                self.redirect('/post/%s' % str(post_id))
                # otherwise if this user is the author of this comment
                # throw an error
            else:
                error = "You cannot edit other users' comments'"
                self.render(
                        "editcomment.html",
                        comment_text=comment.text,
                        edit_error=error)
        # if the user clicks on cancel take the user to the post page
        elif self.request.get("cancel"):
            self.redirect('/post/%s' % str(post_id))

