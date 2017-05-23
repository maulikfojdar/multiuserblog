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

        if post:

            # check if this user is the author of this post
            if self.user and self.user.key().id() == post.user.key().id():
                self.render("editpost.html", post=post)

            # check if the user is logged in
            elif not self.user:
                return self.redirect("/login")

            else:
                self.response.out.write("You cannot edit other user's posts")

        else:
            self.response.out.write("Not a valid post!")

    def post(self, post_id):
        # get the key for this blog post
        key = db.Key.from_path("Post", int(post_id), parent=blog_key())
        post = db.get(key)

        if not self.user:
            return self.redirect('/login')

        if post:

            # if the user clicks on update comment
            if self.user and self.user.key().id() == post.user.key().id():

                # get the subject, content and user when the form is submitted
                subject = self.request.get("subject")
                content = self.request.get("content").replace('\n', '<br>')

                if subject and content:
                    # update the blog post and redirect to the post page
                    post.subject = subject
                    post.content = content
                    post.put()
                    time.sleep(0.1)
                    self.redirect('/post/%s' % str(post.key().id()))

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

        else:
            self.response.out.write("Not a valid post!")
