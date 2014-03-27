# coding=utf-8
from __future__ import unicode_literals

from decimal import Decimal
from sqlalchemy.sql import type_api, sqltypes


class Currency(type_api.TypeDecorator):
    """
    A SQLAlchemy type that accurately saves Decimal values to a fixed number
    of places (2 by default). This is similar to SQLAlchemy's builtin
    Numeric type, but differs in its fallback implementation: Numeric falls
    back on saving as floats, while Currency falls back on saving as integers,
    making it more suitable for database computation (such as SUM, AVG, and
    other SQL functions).

    This type has only been tested to work properly on postgresql (built-in
    numeric support) and sqlite (fallback integer support).
    """
    impl = type_api.TypeEngine

    def __init__(self, precision=None, scale=2, *args, **kwargs):
        self.precision = precision
        self.scale = scale
        self.quantize = Decimal("10") ** -self.scale
        super(Currency, self).__init__(*args, **kwargs)

    def asdecimal(self, dialect):
        return dialect.supports_native_decimal or sqltypes.Numeric in dialect.colspecs

    def load_dialect_impl(self, dialect):
        if self.asdecimal(dialect):
            return dialect.type_descriptor(sqltypes.Numeric)
        else:
            return dialect.type_descriptor(sqltypes.Integer)

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if self.asdecimal(dialect):
            return float(value)
        else:
            # store as an integer
            return int(value / self.quantize)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        d = Decimal(value)
        if self.asdecimal(dialect):
            return d.quantize(self.quantize)
        else:
            # rescale our stored integer
            return d * self.quantize
