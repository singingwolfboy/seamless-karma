from datetime import datetime
from decimal import Decimal
import iso8601
import copy
import six
from flask.ext.restful import fields

TWOPLACES = Decimal(10) ** -2

## marshal fields ##

class TwoDecimalPlaceField(fields.Raw):
    def format(self, value):
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


from .user import *
from .organization import *
from .order import *
from .allocation import *
