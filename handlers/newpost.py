from handlers.handler import Handler
from models.post import Post
from helper import *


class NewPost(Handler):
    def render_page(self, subject="", content="", error=""):
        self.render("newpost.html",
                    subject=subject,
                    content=content,
                    error=error)

    def get(self):
        if self.user:
            self.render_page()
        else:
            self.redirect("/login")

    def post(self):
        if self.user:
            subject = self.request.get("subject")
            content = self.request.get("content")
            user_id = self.user

            if subject and content:
                new_post = Post(parent=blog_key(),
                                subject=subject,
                                content=content,
                                user=user_id)
                new_post.put()
                self.redirect("/post/%s" % str(new_post.key().id()))
            else:
                error = "Both fields are required"
                self.render_page("newpost.html",
                                 subject,
                                 content,
                                 error=error)
        else:
            self.redirect("/login")
