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
        likes = Like.by_post_id(post)
        comments_count = Comment.count_by_post_id(post)
        post_comments = Comment.all_by_post_id(post)
        self.render("post.html",
                    post=post,
                    likes=likes,
                    comments_count=comments_count,
                    post_comments=post_comments)

    def post(self, post_id):
        # get all the necessary parameters
        key = db.Key.from_path("Post", int(post_id), parent=blog_key())
        post = db.get(key)
        user_id = User.by_name(self.user.name)
        comments_count = Comment.count_by_post_id(post)
        post_comments = Comment.all_by_post_id(post)
        likes = Like.by_post_id(post)
        previously_liked = Like.check_like(post, user_id)

        # check if the user is logged in
        if self.user:
            # if the user clicks on like
            if self.request.get("like"):
                # first check if the user is trying to like his own post
                if post.user.key().id() != User.by_name(self.user.name).key().id():
                    # then check if the user has liked this post before
                    if previously_liked == 0:
                        # add like to the likes database and refresh the page
                        l = Like(
                                 post=post,
                                 user=User.by_name(self.user.name))
                        l.put()
                        time.sleep(0.1)
                        self.redirect('/post/%s' % str(post.key().id()))
                    # otherwise if the user has liked this post before throw
                    # and error
                    else:
                        error = "You have already liked this post"
                        self.render(
                                    "post.html",
                                    post=post,
                                    likes=likes,
                                    error=error,
                                    comments_count=comments_count,
                                    post_comments=post_comments)
                # otherwise if the user is trying to like his own post throw an
                # error
                else:
                    error = "You cannot like your own posts"
                    self.render(
                                "post.html",
                                post=post,
                                likes=likes,
                                error=error,
                                comments_count=comments_count,
                                post_comments=post_comments)
            # if the user clicks on add comment get the comment text first
            if self.request.get("add_comment"):
                comment_text = self.request.get("comment_text")
                # check if there is anything entered in the comment text area
                if comment_text:
                    # add comment to the comments database and refresh page
                    c = Comment(post=post,
                                user=User.by_name(self.user.name),
                                text=comment_text)
                    c.put()
                    time.sleep(0.1)
                    self.redirect('/post/%s' % str(post.key().id()))
                # otherwise if nothing has been entered in the text area throw
                # an error
                else:
                    comment_error = "Please enter a comment\
                                        in the text area to post"
                    self.render(
                                "post.html",
                                post=post,
                                likes=likes,
                                comments_count=comments_count,
                                post_comments=post_comments,
                                comment_error=comment_error)
            # if the user clicks on edit post
            if self.request.get("edit"):
                # check if the user is the author of this post
                if post.user.key().id() == \
                            User.by_name(self.user.name).key().id():
                    # take the user to edit post page
                    self.redirect('/edit/%s' % str(post.key().id()))
                    # otherwise if the user is not the author of this post
                    # throw an error
                else:
                    error = "You cannot edit other user's posts"
                    self.render(
                                "post.html",
                                post=post,
                                likes=likes,
                                comments_count=comments_count,
                                post_comments=post_comments,
                                error=error)
            # if the user clicks on delete
            if self.request.get("delete"):
                # check if the user is the author of this post
                if post.user.key().id() == \
                            User.by_name(self.user.name).key().id():
                    # delete the post and redirect to the main page
                    db.delete(key)
                    time.sleep(0.1)
                    self.redirect('/')
                # otherwise if the user is not the author of this post
                # throw an error
                else:
                    error = "You cannot delete other user's posts"
                    self.render(
                                "post.html",
                                post=post,
                                likes=likes,
                                comments_count=comments_count,
                                post_comments=post_comments,
                                error=error)
        # otherwise if the user is not logged in take them to the
        # login page
        else:
            self.redirect("/login")
