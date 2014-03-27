# coding=utf-8
from __future__ import unicode_literals

import copy
import six
from six.moves.urllib.parse import (
    urlsplit, urlunsplit, parse_qsl, urlencode
)


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


def bool_from_str(s):
    if not isinstance(s, six.string_types):
        return bool(s)
    if s.lower() in ("0", "f", "false"):
        return False
    else:
        return True
