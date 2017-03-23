import webapp2
from google.appengine.ext import db
from helper import *

# Models
from models.user import User
from models.post import Post
from models.like import Like
from models.comment import Comment


#Handlers
from handlers.handler import Handler
from handlers.mainpage import MainPage
from handlers.newpost import NewPost
from handlers.signup import Signup
from handlers.login import Login
from handlers.logout import Logout
from handlers.postpage import PostPage
from handlers.editpost import EditPost
from handlers.editcomment import EditComment
from handlers.deletecomment import DeleteComment

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
