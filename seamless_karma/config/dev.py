# development configuration
import os

DEBUG = True
SECRET_KEY = "dummy"
CACHE_NO_NULL_WARNING = True
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///seamless_karma.db")
