from flask.ext.heroku import Heroku
heroku = Heroku()

from raven.contrib.flask import Sentry
sentry = Sentry()

from flask.ext.cache import Cache
cache = Cache()

from flask.ext.restful import Api
api = Api(prefix="/api")
from .restful import *
