from flask import Flask
from flask.ext.heroku import Heroku
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.restful import Api

app = Flask(__name__)
heroku = Heroku(app)
db = SQLAlchemy(app)
api = Api(app, prefix="/api")

from .models import *
from .views import *
from .restful import *
