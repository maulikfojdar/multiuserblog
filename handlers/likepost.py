from google.appengine.ext import db
from models.user import User
from models.post import Post
from models.like import Like
from models.comment import Comment
from handlers.handler import Handler
from helper import *
import time


class LikePost(Handler):

    def get(self, post_id):
        key = db.Key.from_path("Post", int(post_id), parent=blog_key())
        post = db.get(key)
        comments_count = Comment.count_by_post_id(post)
        post_comments = Comment.all_by_post_id(post)

        if post:
            # check if the user is trying to like own post
            if self.user and self.user.key().id() == post.user.key().id():
                error = "You cannot like your own posts"
                self.render("post.html",
                            post=post,
                            comments_count=comments_count,
                            post_comments=post_comments,
                            error=error)
            elif not self.user:
                self.redirect('/login')
            else:
                like = Like.all().filter('user =',
                                         self.user).filter('post =',
                                                           post).get()

                if like:
                    self.redirect('/post/' + str(post.key().id()))

                else:
                    like = Like(post=post,
                                user=self.user)

                    post.likes += 1

                    like.put()
                    post.put()

                    self.redirect('/post/' + str(post.key().id()))

        else:
            self.response.out.write("Not a valid post!")
