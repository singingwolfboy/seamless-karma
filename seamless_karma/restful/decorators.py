# coding=utf-8
from __future__ import unicode_literals

import re
from functools import wraps
from six.moves.urllib.parse import urlsplit
from textwrap import dedent

import sqlalchemy as sa
from seamless_karma.extensions import db
from flask import request
from flask.ext.restful import abort, marshal
from .utils import update_url_query


def parse_sqlalchemy_exception(exception, model=None):
    """
    Given a SQLAlchemy exception, return a string to nicely display to the
    client that explains the error.
    """
    message = exception.orig.args[0]
    if not model:
        return message
    if db.engine.name == 'postgresql':
        re_strs = [
            r"""
            duplicate key value violates unique constraint "[^"]+"
            DETAIL:  Key \((?P<column>[^)]+)\)=\((?P<value>[^)]+)\) already exists.
            """
        ]
        UNIQUE_RES = [re.compile(dedent(s).strip()) for s in re_strs]
        NOT_NULL_RES = []
    else:  # sqlite
        unique_re_strs = [
            r"column (?P<column>\w+) is not unique",
            r"UNIQUE constraint failed: (?P<table>\w+)\.(?P<column>\w+)",
        ]
        not_null_re_strs = [
            r"NOT NULL constraint failed: (?P<table>\w+)\.(?P<column>\w+)",
        ]
        UNIQUE_RES = [re.compile(dedent(s).strip()) for s in unique_re_strs]
        NOT_NULL_RES = [re.compile(dedent(s).strip()) for s in not_null_re_strs]
    for regex in UNIQUE_RES:
        match = regex.search(message)
        if match:
            column = match.group("column")
            try:
                value = match.group("value")
            except IndexError:
                value = request.form.get(column)
            return "{model} with {column} {value} already exists".format(
                model=model.__name__, column=column, value=value
            )
    for regex in NOT_NULL_RES:
        match = regex.search(message)
        if match:
            column = match.group("column")
            return "{model} must have {column} specified".format(
                model=model.__name__, column=column
            )
    return message


def handle_sqlalchemy_errors(cls):
    model = getattr(cls, "model", None)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except sa.exc.SQLAlchemyError as e:
                message = parse_sqlalchemy_exception(e, model)
                abort(400, message=message)
        return wrapper

    if not hasattr(cls, "method_decorators"):
        cls.method_decorators = []
    cls.method_decorators.append(decorator)
    return cls


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
