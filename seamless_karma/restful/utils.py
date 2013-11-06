from datetime import datetime
from decimal import Decimal
import iso8601
import copy
import six
from flask import request
from flask.ext.restful import fields, reqparse, abort

## marshal fields ##

TWOPLACES = Decimal(10) ** -2

class TwoDecimalPlaceField(fields.Raw):
    def format(self, value):
        if isinstance(value, int):
            value = Decimal(value)
        rounded = value.quantize(TWOPLACES)
        return six.text_type(rounded)


class ISOFormatField(fields.Raw):
    def format(self, value):
        return value.isoformat()


## reqparse types ##

def string_or_int_type(value, name):
    """
    If the first character is a number, parse as an integer.
    Otherwise, assume string.
    """
    if value[0].isdigit():
        try:
            return int(value)
        except ValueError:
            raise ValueError(u"{} string may not start with a number".format(name))
    else:
        return value


def date_type(value, name):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(u"{} string must be a YYYY-MM-DD formatted date".format(name))


def datetime_type(value, name):
    try:
        return iso8601.parse_date(value)
    except:
        raise ValueError(u"{} string must be an ISO-8601 formatted datetime")

## utility functions ##

def make_optional(parser):
    """
    Returns a copy of the parser, with all of its arguments set to
    required=False and default=None. Useful for API endpoints that do
    partial updates to resources.
    """
    p2 = copy.deepcopy(parser)
    args = []
    for arg in p2.args:
        arg.required = False
        arg.default = None
        args.append(arg)
    p2.args = args
    return p2


def paginate_query(query, order_cls=None, default_limit=50, max_limit=200):
    """
    Apply `limit`, `offset`, and `order_by` to query, if specified.
    """
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
    else:
        limit = default_limit
    query = query.limit(limit)

    if "offset" in request.values:
        try:
            offset = int(request.values["offset"])
        except ValueError:
            abort(400, "offset must be an integer, not {!r}".format(
                request.values["limit"]))
        if limit < 0:
            abort(400, "offset cannot be negative")
        query = query.offset(offset)

    if order_cls:
        if "order" in request.values:
            orders = []
            for order_str in request.values["order"].split(','):
                if not hasattr(order_cls, order_str):
                    abort(400, "cannot order on attribute {!r}".format(order_str))
                orders.append(getattr(order_cls, order_str))
            query = query.order_by(*orders)
        else:
            query = query.order_by(order_cls.id)

    return query


