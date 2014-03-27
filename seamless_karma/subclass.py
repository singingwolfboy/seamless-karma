# coding=utf-8
from __future__ import unicode_literals

from datetime import datetime
from decimal import Decimal
from functools import wraps
import six
import iso8601
from flask.ext.restful import Api as BaseApi
from flask.ext.restful import fields

## Api subclass that does CORS ##

def cors(func):
    """
    Decorator that allows Cross-Origin Resource Sharing
    http://www.html5rocks.com/en/tutorials/cors/
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    return wrapper


class Api(BaseApi):
    def __init__(self, app=None, prefix='',
                 default_mediatype='application/json', decorators=None,
                 catch_all_404s=False, url_part_order='bae'):
        super(Api, self).__init__(
            app, prefix, default_mediatype, decorators, catch_all_404s,
            url_part_order
        )
        self.decorators.append(cors)

    @cors
    def handle_error(self, e):
        return super(Api, self).handle_error(e)

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

