from datetime import datetime
from decimal import Decimal
import iso8601
import copy
import six
from flask import request
from flask.ext.restful import fields, reqparse, abort
try:
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
except ImportError:
    from urlparse import urlsplit, urlunsplit, parse_qsl
    from urllib import urlencode

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


def update_url_query(*args, **kwargs):
    """
    Return a new URL with the query parameters of the URL updated based on the
    keyword arguments of the function call. If the argument already exists in the
    URL, it will be overwritten with the new value; if not, it will be added.
    However, if the new value is None, then any existing query parameters with
    that key will be removed without being replaced.

    The URL must be passed as the first positional argument of the function;
    it cannot be passed as a keyword argument.
    """
    if not args:
        raise TypeError("URL must be passed as the first positional argument")
    url = args[0]
    scheme, netloc, path, query, fragment = urlsplit(url)
    qlist = parse_qsl(query)
    for key, value in kwargs.items():
        # remove all key/value pairs from qlist that match this key
        qlist = [pair for pair in qlist if not pair[0] == key]
        # add this key/value pair to the qlist (unless it's None)
        if value is not None:
            qlist.append((key, value))
    # bring it on back
    query = urlencode(qlist)
    return urlunsplit((scheme, netloc, path, query, fragment))
