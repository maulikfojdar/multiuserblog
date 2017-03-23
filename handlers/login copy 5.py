import webapp2
import os
import jinja2
import re
import hashlib
import hmac
import random
import time
from string import letters
from google.appengine.ext import db

# Models
from models.user import User
from models.post import Post
from models.like import Like
from models.comment import Comment

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

secret = "secret"

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")


def valid_username(username):
    return USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")


def valid_password(password):
    return PASS_RE.match(password)

EMAIL_RE = re.compile(r"[\S]+@[\S]+.[\S]+$")


def valid_email(email):
    return EMAIL_RE.match(email)


def make_secure_val(val):
    return "%s|%s" % (val, hmac.new(secret, val).hexdigest())


def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val


def make_salt(length=5):
    return ''.join(random.choice(letters) for x in xrange(length))


def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)


def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)


def users_key(group='default'):
    return db.Key.from_path('users', group)


def blog_key(name='default'):
    return db.Key.from_path('Blog', name)


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


class Handler(webapp2.RequestHandler):
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')


class User(db.Model):
    name = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)
    email = db.StringProperty()

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent=users_key())

    @classmethod
    def by_name(cls, name):
        u = User.all().filter('name =', name).get()
        return u

    @classmethod
    def register(cls, name, pw, email=None):
        pw_hash = make_pw_hash(name, pw)
        return User(parent=users_key(),
                    name=name,
                    pw_hash=pw_hash,
                    email=email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u


class Post(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)
    user = db.ReferenceProperty(User,
                                required=True,
                                collection_name="posts")

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", post=self)


class Comment(db.Model):
    post = db.ReferenceProperty(Post, required=True)
    user = db.ReferenceProperty(User, required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    text = db.TextProperty(required=True)

    # get number of comments for a post
    @classmethod
    def count_by_post_id(cls, post):
        c = Comment.all().filter('post =', post)
        return c.count()

    # get all comments for a specific post
    @classmethod
    def all_by_post_id(cls, post):
        c = Comment.all().filter('post =', post).order('created')
        return c


class Like(db.Model):
    post = db.ReferenceProperty(Post, required=True)
    user = db.ReferenceProperty(User, required=True)
    
    # get number of likes for a blog id
    @classmethod
    def by_post_id(cls, post_id):
        l = Like.all().filter('post =', post_id)
        return l.count()
    
    # get number of likes for a blog and user id
    @classmethod
    def check_like(cls, post_id, user_id):
        cl = Like.all().filter('post =', \
                               post_id).filter('user =', user_id)
        return cl.count()


class Unlike(db.Model):
    post = db.ReferenceProperty(Post, required=True)
    user = db.ReferenceProperty(User, required=True)
    
    # get number of unlikes for a blog id
    @classmethod
    def by_post_id(cls, post_id):
        ul = Unlike.all().filter('post =', post_id)
        return ul.count()
    
    # get number of unlikes for a blog and user id
    @classmethod
    def check_unlike(cls, post_id, user_id):
        cul = Unlike.all().filter('post =', \
                                  post_id).filter('user =', user_id)
        return cul.count()


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
                             subject, content,
                             error=error)
        else:
            self.redirect("/login")


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


class DeleteComment(Handler):
    def get(self, post_id, comment_id):
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


class MainPage(Handler):
    def get(self):
            posts = db.GqlQuery("SELECT * FROM Post ORDER BY created DESC")
            if posts:
                self.render("main.html", posts=posts)


class Signup(Handler):
    def get(self):
        self.render("signup.html")

    def post(self):
        have_error = False
        username = self.request.get("username")
        password = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")

        params = dict(username=username, email=email)

        if not valid_username(username):
            params['error_username'] = "That's not a valid username"
            have_error = True

        if not valid_password(password):
            params['error_password'] = "That's not a valid password"
            have_error = True
        elif password != verify:
            params['error_verify'] = "The passwords do not match!"
            have_error = True

        if have_error:
            self.render("signup.html", **params)
        else:
            u = User.by_name(username)
            if u:
                msg = 'That user already exists.'
                self.render('signup.html', error_username=msg)
            else:
                u = User.register(username, password, email)
                u.put()
                self.login(u)
                self.redirect('/')


class Register(Signup):
    def done(self):
        # make sure the user doesn't already exist
        u = User.by_name(self.username)
        if u:
            msg = 'That user already exists.'
            self.render('signup.html', error_username=msg)
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()
            self.login(u)
            self.redirect('/')


class Login(Handler):
    def get(self):
        self.render('login.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/')
        else:
            msg = 'Invalid login'
            self.render('login.html', error=msg)


class Logout(Handler):
    def get(self):
        self.logout()
        self.redirect('/')


class PostPage(Handler):
    def get(self, post_id):
        post = db.get(db.Key.from_path("Post",
                                       int(post_id),
                                       parent=blog_key()))
        likes = Like.by_post_id(post)
        unlikes = Unlike.by_post_id(post)
        comments_count = Comment.count_by_post_id(post)
        post_comments = Comment.all_by_post_id(post)
        self.render("post.html",
                    post=post,
                    likes=likes,
                    unlikes=unlikes,
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
        unlikes = Unlike.by_post_id(post)
        previously_liked = Like.check_like(post, user_id)
        previously_unliked = Unlike.check_unlike(post, user_id)

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
                                    unlikes=unlikes,
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
                                unlikes=unlikes,
                                error=error,
                                comments_count=comments_count,
                                post_comments=post_comments)
            # if the user clicks on unlike
            if self.request.get("unlike"):
                # first check if the user is trying to unlike his own post
                if post.user.key().id() != User.by_name(self.user.name).key().id():
                    # then check if the user has unliked this post before
                    if previously_unliked == 0:
                        # add unlike to the unlikes database and refresh the
                        # page
                        ul = Unlike(post=post,
                                    user=User.by_name(self.user.name))
                        ul.put()
                        time.sleep(0.1)
                        self.redirect('/post/%s' % str(post.key().id()))
                    # otherwise if the user has unliked this post before throw
                    # and error
                    else:
                        error = "You have already unliked this post"
                        self.render(
                                    "post.html",
                                    post=post,
                                    likes=likes,
                                    unlikes=unlikes,
                                    error=error,
                                    comments_count=comments_count,
                                    post_comments=post_comments)
                # otherwise if the user is trying to unlike his own post throw
                # an error
                else:
                    error = "You cannot unlike your own posts"
                    self.render(
                                "post.html",
                                post=post,
                                likes=likes,
                                unlikes=unlikes,
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
                                unlikes=unlikes,
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
                                unlikes=unlikes,
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
                                unlikes=unlikes,
                                comments_count=comments_count,
                                post_comments=post_comments,
                                error=error)
        # otherwise if the user is not logged in take them to the
        # login page
        else:
            self.redirect("/login")


app = webapp2.WSGIApplication([
   ('/', MainPage),
   ('/newpost', NewPost),
   ('/signup', Signup),
   ('/login', Login),
   ('/logout', Logout),
   ('/post/([0-9]+)', PostPage),
   ('/edit/([0-9]+)', EditPost),
   ('/post/([0-9]+)/editcomment/([0-9]+)',EditComment),
   ('/post/([0-9]+)/deletecomment/([0-9]+)',DeleteComment)
], debug=True)
