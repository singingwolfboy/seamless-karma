from seamless_karma.models import db, User, Order, OrderContribution
from seamless_karma.extensions import api
import sqlalchemy as sa
from flask import request, url_for
from flask.ext.restful import Resource, abort, fields, marshal_with, reqparse
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
import copy
import six
from .utils import (TwoDecimalPlaceField, TWOPLACES, ISOFormatField,
    date_type, datetime_type)
from .decorators import handle_sqlalchemy_errors, resource_list


class OrderContributionField(fields.Raw):
    def format(self, value):
        return [{
            "user_id": oc.user_id,
            "total": six.text_type(oc.amount.quantize(TWOPLACES)),
        } for oc in value]


mfields = {
    "id": fields.Integer,
    "seamless_id": fields.Integer(default=None),
    "vendor_id": fields.Integer,
    "ordered_by": fields.Integer(attribute="ordered_by_id"),
    "for_date": ISOFormatField,
    "placed_at": ISOFormatField,
    "total": TwoDecimalPlaceField(attribute="total_amount"),
    "contributions": OrderContributionField,
}

class ContributionArgument(reqparse.Argument):
    def __init__(self, dest="contributions", required=False, default=None,
                 ignore=False, help=None):
        self.dest = dest
        self.required = required
        self.default = default or {}
        self.ignore = ignore
        self.help = help

    def convert_amount(self, value):
        try:
            return Decimal(value)
        except InvalidOperation:
            raise ValueError("contributed_amount must be a decimal, "
                "not {!r}".format(value))

    def convert_user_id(self, value):
        try:
            return int(value)
        except ValueError:
            try:
                user = User.query.filter(User.username == value).one()
            except sa.orm.exc.NoResultFound:
                raise ValueError("contributed_by must be a user ID or username; "
                    "{!r} is not a user ID, and no user exists with "
                    "that username".format(value))
            else:
                return user.id

    def convert(self, request):
        amounts = [self.convert_amount(value)
            for value in request.values.getlist('contributed_amount')]
        user_ids = [self.convert_user_id(value)
            for value in request.values.getlist('contributed_by')]
        if len(amounts) != len(user_ids):
            raise ValueError("must pass equal number of "
                "contributed_by and contributed_amount arguments")
        if len(user_ids) != len(set(user_ids)):
            raise ValueError("contributed_by values may not contain duplicates")
        if self.required and not user_ids:
            raise ValueError("at least one pair of contributed_by and "
                "contributed_amount values is required")
        return dict(zip(user_ids, amounts))

    def parse(self, request):
        try:
            return self.convert(request)
        except Exception as error:
            if self.ignore:
                return self.default
            self.handle_validation_error(error)


user_order_parser = reqparse.RequestParser()
user_order_parser.args.append(ContributionArgument(required=True))
user_order_parser.add_argument('for_date', type=date_type, default=date.today())
user_order_parser.add_argument('placed_at', type=datetime_type, default=datetime.now())
user_order_parser.add_argument('vendor_id', int)
user_order_parser.add_argument('seamless_id', int)

order_parser = copy.deepcopy(user_order_parser)
order_parser.add_argument('ordered_by_id', type=int, required=True)


class OrderList(Resource):
    method_decorators = [handle_sqlalchemy_errors]

    @resource_list(Order, mfields)
    def get(self):
        return Order.query

    def post(self):
        args = order_parser.parse_args()
        order = Order.create(**args)
        db.session.add(order)
        db.session.commit()
        location = url_for('order', order_id=order.id)
        return {"message": "created", "id": order.id}, 201, {"Location": location}


class OrderDetail(Resource):
    method_decorators = [handle_sqlalchemy_errors]

    def get_order_or_abort(self, id):
        o = Order.query.get(id)
        if not o:
            abort(404, message="Order {} does not exist".format(id))
        return o

    @marshal_with(mfields)
    def get(self, order_id):
        return self.get_order_or_abort(order_id)

    @marshal_with(mfields)
    def put(self, order_id):
        o = self.get_order_or_abort(order_id)
        args = make_optional(order_parser).parse_args()
        for attr in ('seamless_id', 'vendor_id', 'ordered_by_id', 'for_date', 'placed_at'):
            if attr in args:
                setattr(u, attr, args[attr])
        if args.contributions:
            o.contributions = [OrderContribution(user_id=c.user_id, amount=amount, order=o)
                for user_id, amount in args.contributions.items()]
        db.session.add(o)
        db.session.commit()
        return o

    def delete(self, order_id):
        o = self.get_order_or_abort(order_id)
        db.session.delete(o)
        db.session.commit()
        return {"message": "deleted"}, 200


class UserOrderList(Resource):
    method_decorators = [handle_sqlalchemy_errors]

    @resource_list(Order, mfields)
    def get(self, user_id):
        return Order.query.filter(Order.user_id == user_id)

    def post(self, user_id):
        args = user_order_parser.parse_args()
        args['ordered_by_id'] = user_id
        order = Order.create(**args)
        db.session.add(order)
        db.session.commit()
        location = url_for('order', order_id=order.id)
        return {"message": "created", "id": order.id}, 201, {"Location": location}


class OrganizationOrderList(Resource):
    method_decorators = [handle_sqlalchemy_errors]

    @resource_list(Order, mfields)
    def get(self, org_id):
        return (Order.query
            .join(User)
            .filter(User.organization_id == org_id)
        )


class OrganizationOrderListForDate(Resource):
    method_decorators = [handle_sqlalchemy_errors]

    @resource_list(Order, mfields)
    def get(self, org_id, for_date):
        return (Order.query
            .join(User)
            .filter(User.organization_id == org_id)
            .filter(Order.for_date == for_date)
        )


api.add_resource(OrderList, "/orders")
api.add_resource(OrderDetail, "/orders/<int:order_id>")
api.add_resource(UserOrderList, "/users/<int:user_id>/orders")
api.add_resource(OrganizationOrderList, "/organizations/<int:org_id>/orders")
api.add_resource(OrganizationOrderListForDate,
    "/organizations/<int:org_id>/orders/<date:for_date>")
