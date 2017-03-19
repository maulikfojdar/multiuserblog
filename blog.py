import webapp2
import os
import jinja2
import re
import hashlib
import hmac
import random
from string import letters
from google.appengine.ext import db

template_dir= os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

secret= "secret"

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
    
def make_salt(length = 5):
    return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' %  (salt, h)

def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)

def users_key(group = 'default'):
    return db.Key.from_path('users', group)

def blog_key(name = 'default'):
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
    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = users_key())

    @classmethod
    def by_name(cls, name):
        u = User.all().filter('name =', name).get()
        return u

    @classmethod
    def register(cls, name, pw, email = None):
        pw_hash = make_pw_hash(name, pw)
        return User(parent = users_key(),
                    name = name,
                    pw_hash = pw_hash,
                    email = email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u

    
class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now=True)
    user = db.ReferenceProperty(User,
                                required=True,
                                collection_name="posts")

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", post=self)

class NewPost(Handler):
    def render_page(self, subject="", content="", error=""):
        self.render("newpost.html",subject=subject, content=content, error=error)
        
    def get(self):
        if self.user:
            self.render_page()
        else:
            self.redirect("/login")

    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")
        user_id = User.by_name(self.user.name)

        if subject and content:
            new_post = Post(parent = blog_key(), subject = subject, content = content, user = user_id)
            new_post.put()
            self.redirect("/post/%s" % str(new_post.key().id()))
        else:
            error = "Both fields are required"
            self.render_page("newpost.html", subject, content, error = error)
            
class MainPage(Handler):
    def get(self):
        if self.user:
            posts = db.GqlQuery("SELECT * FROM Post ORDER BY created DESC")
            self.render("main.html", posts = posts, username = self.user.name)
        else:
            self.redirect("/signup");

class Signup(Handler):
    def get(self):
        self.render("signup.html")

    def post(self):
        have_error = False
        username = self.request.get("username")
        password = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")

        params = dict(username = username, email = email)

        if not valid_username(username):
            params['error_username'] = "That's not a valid username"
            have_error = True

        if not valid_password(password):
            params['error_password'] = "That's not a valid password"
            have_error = True
        elif password != verify:
            params['error_verify'] = "The passwords do not match!"
            have_error=True

        if have_error:
            self.render("signup.html", **params)
        else:
            #self.redirect("/?username="+username)
            u = User.by_name(username)
            if u:
                msg = 'That user already exists.'
                self.render('signup.html', error_username = msg)
            else:
                u = User.register(username, password, email)
                u.put()
                self.login(u)
                self.redirect('/')

class Register(Signup):
    def done(self):
        #make sure the user doesn't already exist
        u = User.by_name(self.username)
        if u:
            msg = 'That user already exists.'
            self.render('signup.html', error_username = msg)
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
            self.render('login.html', error = msg)

class Logout(Handler):
    def get(self):
        self.logout()
        self.redirect('/')
        
class PostPage(Handler):
    def get(self, post):
        p = db.get(db.Key.from_path("Post", int(post), parent=blog_key()))
        self.render("post.html", subject = p.subject, content = p.content,
                    created = p.created)
         
app = webapp2.WSGIApplication([('/', MainPage),
                               ('/newpost', NewPost),
                               ('/signup', Signup),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/post/([0-9]+)', PostPage)], debug=True)
