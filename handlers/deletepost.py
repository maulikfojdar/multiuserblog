from google.appengine.ext import db
from models.user import User
from models.post import Post
from models.like import Like
from models.comment import Comment
from handlers.handler import Handler
from helper import *
import time


class DeletePost(Handler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if self.user and self.user.key().id() == post.user.key().id():

            if post:
                db.delete(key)
                time.sleep(0.1)
                self.redirect('/')
            else:
                self.response.out.write("Not a valid post!")
        # otherwise if the user is not logged in take them to the
        # login page
        elif not self.user:
            self.redirect("/login")
        else:
            error = "You cannot delete other user's posts"

            likes = like = Like.all().filter('post_id =', post_id).get()
            comments_count = Comment.count_by_post_id(post)
            post_comments = Comment.all_by_post_id(post)
            self.render("post.html",
                        post=post,
                        likes=likes,
                        comments_count=comments_count,
                        post_comments=post_comments,
                        error=error)
