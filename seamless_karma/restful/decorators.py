import sqlalchemy as sa
from functools import wraps
from flask import request
from flask.ext.restful import abort, marshal
try:
    from urllib.parse import urlparse, urlunparse
except ImportError:
    from urlparse import urlparse, urlunparse


def handle_sqlalchemy_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sa.exc.SQLAlchemyError as e:
            abort(400, message=e.message)
    return wrapper


def resource_list(model, marshal_fields, default_limit=50, max_limit=200):
    def outer(func):
        @wraps(func)
        def inner(*args, **kwargs):
            # parse values before processing function
            limit = default_limit
            if "limit" in request.values:
                try:
                    limit = int(request.values["limit"])
                except ValueError:
                    abort(400, "limit must be an integer, not {!r}".format(
                        request.values["limit"]))
                if limit < 1:
                    abort(400, "limit must be greater than 0")
                if max_limit and limit > max_limit:
                    abort(400, "maximum limit is {}".format(max_limit))

            offset = None
            if "offset" in request.values:
                try:
                    offset = int(request.values["offset"])
                except ValueError:
                    abort(400, "offset must be an integer, not {!r}".format(
                        request.values["limit"]))
                if offset < 0:
                    abort(400, "offset cannot be negative")

            orders = []
            if "order" in request.values:
                for order_str in request.values["order"].split(','):
                    if not hasattr(model, order_str):
                        abort(400, "cannot order on attribute {!r}".format(order_str))
                    orders.append(getattr(model, order_str))
            elif hasattr(model, "id"):
                orders.append(model.id)

            # process the function
            query = func(*args, **kwargs)

            # build the results
            total = query.count()
            values = query.order_by(*orders).limit(limit).offset(offset).all()
            return {
                "total": total,
                "data": marshal(values, marshal_fields),
            }
        return inner
    return outer
