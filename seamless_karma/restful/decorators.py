from functools import wraps
try:
    from urllib.parse import urlsplit
except ImportError:
    from urlparse import urlsplit

import sqlalchemy as sa
from flask import request
from flask.ext.restful import abort, marshal
from .utils import update_url_query


def handle_sqlalchemy_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sa.exc.SQLAlchemyError as e:
            abort(400, message=e.message)
    return wrapper


def resource_list(model, marshal_fields, default_limit=50, max_limit=200, parser=None):
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

            # allow users to filter by parser fields
            if parser:
                for name, value in parser.parse_args().items():
                    if hasattr(model, name) and value is not None:
                        query = query.filter(getattr(model, name) == value)

            # build the results
            count = query.count()
            results = query.order_by(*orders).limit(limit).offset(offset).all()
            output = {
                "count": count,
                "data": marshal(results, marshal_fields),
            }
            # just get path and query args from URL
            scheme, netloc, path, query, fragment = urlsplit(request.url)
            url = "{path}?{query}".format(path=path, query=query)
            offset = offset or 0
            if count > offset + limit:
                output["next"] = update_url_query(url, offset=offset+limit)
            if offset > 0:
                new_offset = offset - limit
                if new_offset <= 0:
                    new_offset = None
                output["prev"] = update_url_query(url, offset=new_offset)
            return output

        return inner
    return outer
