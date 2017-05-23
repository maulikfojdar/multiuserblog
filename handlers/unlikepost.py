from google.appengine.ext import db
from models.user import User
from models.post import Post
from models.like import Like
from models.comment import Comment
from handlers.handler import Handler
from helper import *
import time


class UnlikePost(Handler):

    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        comments_count = Comment.count_by_post_id(post)
        post_comments = Comment.all_by_post_id(post)

        if post:
            if self.user and self.user.key().id() == post.user.key().id():
                error = "You cannot dislike your own post"
                self.render("post.html",
                            post=post,
                            comments_count=comments_count,
                            post_comments=post_comments,
                            error=error)
            elif not self.user:
                self.redirect('/login')
            else:
                l = Like.all().filter('user =',
                                      self.user).filter('post =',
                                                        post).get()

                if l:
                    l.delete()
                    post.likes -= 1
                    post.put()

                    self.redirect('/post/' + str(post.key().id()))
                else:
                    self.redirect('/post/' + str(post.key().id()))
