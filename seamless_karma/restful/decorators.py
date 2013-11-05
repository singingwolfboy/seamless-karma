import sqlalchemy as sa
from functools import wraps
from flask.ext.restful import abort


def handle_sqlalchemy_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sa.exc.SQLAlchemyError as e:
            abort(400, message=e.message)
    return wrapper
