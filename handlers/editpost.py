from google.appengine.ext import db
import time
# Models
from models.user import User
from models.post import Post
from models.like import Like
from models.comment import Comment
from handlers.handler import Handler
from helper import *


class EditPost(Handler):
    def get(self, post_id):
        key = db.Key.from_path("Post", int(post_id), parent=blog_key())
        post = db.get(key)
        if not post:
            return self.redirect("/login")

        # check if the user is logged in
        if self.user:
            # check if this user is the author of this post
            if post.user.key().id() == User.by_name(self.user.name).key().id():
                # take the user to the edit post page
                self.render("editPost.html", post=post)
            # otherwise if this user is not the author of this post throw an
            # error
            else:
                self.response.out.write("You cannot edit other user's posts")
        # otherwise if the user is not logged in take them to the login page
        else:
            self.redirect("/login")

    def post(self, post_id):
        # get the key for this blog post
        key = db.Key.from_path("Post", int(post_id), parent=blog_key())
        post = db.get(key)
        if not post:
            return self.redirect("/login")

        # if the user clicks on update comment
        if self.request.get("update"):

            # get the subject, content and user id when the form is submitted
            subject = self.request.get("subject")
            content = self.request.get("content").replace('\n', '<br>')

            # check if this user is the author of this post
            if post.user.key().id() == User.by_name(self.user.name).key().id():
                # check if both the subject and content are filled
                if subject and content:
                    # update the blog post and redirect to the post page
                    post.subject = subject
                    post.content = content
                    post.put()
                    time.sleep(0.1)
                    self.redirect('/post/%s' % str(post.key().id()))
                # otherwise if both subject and content are not filled throw an
                # error
                else:
                    post_error = "Please enter a subject and the blog content"
                    self.render(
                                "editpost.html",
                                subject=subject,
                                content=content,
                                post_error=post_error)
                    # otherwise if this user is not the author of this post
                    # throw an error
            else:
                self.response.out.write("You cannot edit other user's posts")
        # if the user clicks cancel take them to the post page
        elif self.request.get("cancel"):
            self.redirect('/post/%s' % str(post.key().id()))
