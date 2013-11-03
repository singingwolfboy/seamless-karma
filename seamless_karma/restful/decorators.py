from functools import wraps
from flask.ext.restful import abort
from sqlalchemy.exc import SQLAlchemyError


def handle_sqlalchemy_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            abort(400, message=e.message)
    return wrapper
