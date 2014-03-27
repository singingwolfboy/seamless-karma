# coding=utf-8
from __future__ import unicode_literals

from werkzeug.routing import BaseConverter, ValidationError
from datetime import datetime


class ISODateConverter(BaseConverter):
    def to_python(self, value):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            raise ValidationError()

    def to_url(self, value):
        return value.isoformat()
