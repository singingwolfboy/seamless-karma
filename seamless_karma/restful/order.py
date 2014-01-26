from seamless_karma.models import User, Order, OrderContribution
from seamless_karma.extensions import db, api
import sqlalchemy as sa
from flask import url_for
from flask.ext.restful import Resource, abort, fields, marshal_with, reqparse
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
import copy
import six
from .utils import (
    TwoDecimalPlaceField, TWOPLACES, ISOFormatField,
    date_type, datetime_type, make_optional)
from .decorators import handle_sqlalchemy_errors, resource_list


class OrderContributionField(fields.Raw):
    def format(self, value):
        return [{
            "user_id": oc.user_id,
            "amount": six.text_type(oc.amount.quantize(TWOPLACES)),
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
user_order_parser.add_argument('vendor_id', type=int)
user_order_parser.add_argument('seamless_id', type=int)

order_parser = copy.deepcopy(user_order_parser)
order_parser.add_argument('ordered_by_id', type=int, required=True)


@handle_sqlalchemy_errors
class OrderList(Resource):
    model = Order

    @resource_list(Order, mfields)
    def get(self):
        """
        Return a list of all orders.

        Example response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
              "count": 2,
              "data": [
                {
                  "id": 1,
                  "seamless_id": 23452,
                  "vendor_id": 7,
                  "ordered_by": 3,
                  "for_date": "2014-04-01",
                  "placed_at": "2014-03-28T14:23:33Z",
                  "total": "8.49",
                  "contributions": [
                    {
                      "user_id": 3,
                      "amount": "8.49"
                    }
                  ]
                }, {
                  "id": 2,
                  "seamless_id": 342534,
                  "vendor_id": 3,
                  "ordered_by": 4,
                  "for_date": "2014-03-29",
                  "placed_at": "2014-03-29T08:12:10Z",
                  "total": "13.30",
                  "contributions": [
                    {
                      "user_id": 4,
                      "amount": "10.00"
                    }, {
                      "user_id": 8,
                      "amount": "2.00"
                    }, {
                      "user_id": 1,
                      "amount": "1.30"
                    }
                  ]
                }
              ]
            }
        """
        return Order.query

    def post(self):
        """
        Create a new order.

        :form ordered_by_id: *Required* The ID of the user that placed the
            order on Seamless_
        :form seamless_id: *Required* The ID of this order on Seamless_
        :form vendor_id: *Required* The ID of the vendor (restaunt) that took
            this order
        :form for_date: *Optional* The date that the order should be delivered,
            formatted as an ISO8601 date string (YYYY-MM-DD). Defaults to the
            current day.
        :form placed_at: *Optional* The time that the order was placed on
            Seamless_ as an ISO8601 date-time string (YYYY-MM-DDTHH:MM:SSZ).
            Defaults to the moment that this request was received by the server.
        :form contributed_by, contributed_amount: You must supply information about who
            contributed to this order, and how much they contributed to it.
            You must pass pairs of ``contributed_by`` and ``contributed_amount``
            form parameters, where ``contributed_by`` is a user ID and
            ``contributed_amount`` is a dollar amount for that user. At least
            one pair is required. Users and amounts will be associated with
            each other based on position in the list of form parameters.

        Example request:

        .. sourcecode:: http

            POST /api/orders HTTP/1.1
            Host: seamlesskarma.com
            Content-Type: application/x-www-form-urlencoded
            Content-Length: 147

            seamless_id=12345&vendor_id=3&for_date=2013-04-21&contributed_by=4&contributed_amount=8.50&ordered_by_id=4&contributed_by=8&contributed_amount=2.75

        Example response:

        .. sourcecode:: http

            HTTP/1.1 201 CREATED
            Content-Type: application/json
            Location: /api/orders/17

            {
              "message": "created",
              "id": 17
            }

        :status 201: the order was successfully created

        .. _Seamless: http://www.seamless.com
        """
        args = order_parser.parse_args()
        order = Order.create(**args)
        db.session.add(order)
        db.session.commit()
        location = url_for('orderdetail', order_id=order.id)
        return {"message": "created", "id": order.id}, 201, {"Location": location}


@handle_sqlalchemy_errors
class OrderDetail(Resource):
    model = Order

    def get_order_or_abort(self, id):
        o = Order.query.get(id)
        if not o:
            abort(404, message="Order {} does not exist".format(id))
        return o

    @marshal_with(mfields)
    def get(self, order_id):
        """
        Return information about a specific order, identified by ID.

        Example response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
              "id": 2,
              "seamless_id": 342534,
              "vendor_id": 3,
              "ordered_by": 4,
              "for_date": "2014-03-29",
              "placed_at": "2014-03-29T08:12:10Z",
              "total": "13.30",
              "contributions": [
                {
                  "user_id": 4,
                  "amount": "10.00"
                }, {
                  "user_id": 8,
                  "amount": "2.00"
                }, {
                  "user_id": 1,
                  "amount": "1.30"
                }
              ]
            }

        :status 200: no error
        :status 404: there is no order with the given ID
        """
        return self.get_order_or_abort(order_id)

    @marshal_with(mfields)
    def put(self, order_id):
        """
        Update information about a specific order, identified by ID.

        Example request:

        .. sourcecode:: http

            PUT /api/orders/42 HTTP/1.1
            Host: seamlesskarma.com
            Content-Type: application/x-www-form-urlencoded
            Content-Length: 17

            seamless_id=54321

        Example response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
              "id": 42,
              "seamless_id": 54321,
              "vendor_id": 2,
              "ordered_by": 14,
              "for_date": "2014-02-29",
              "placed_at": "2014-03-29T08:12:10Z",
              "total": "13.30",
              "contributions": [
                {
                  "user_id": 14,
                  "amount": "11.10"
                }, {
                  "user_id": 3,
                  "amount": "2.10"
                }
              ]
            }

        :form seamless_id: *Optional* updated Seamless ID
        :form vendor_id: *Optional* updated vendor ID
        :form ordered_by_id: *Optional* updated user ID of the user who placed
            this order
        :form for_date: *Optional* updated date that the order should be delivered
        :form placed_at: *Optional* updated datetime when the order was
            placed
        :form contributed_by, contributed_amount: *Optional* updated pairs of
            contribution information. If any pairs are passed, they overwrite
            existing contribution information, meaning that if you do not include
            a specific user's contribution in your update, that contribution
            will be removed from this order.
        :status 200: the order was updated
        :status 404: there is no user with the given ID
        """

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
        """
        Delete a specific order, identified by ID.

        Example response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
              "message": "deleted"
            }

        :status 200: the order was deleted
        :status 404: there is no order with the given ID
        """
        o = self.get_order_or_abort(order_id)
        db.session.delete(o)
        db.session.commit()
        return {"message": "deleted"}, 200


@handle_sqlalchemy_errors
class UserOrderList(Resource):
    model = Order

    @resource_list(Order, mfields)
    def get(self, user_id):
        """
        Get all orders ordered by the user identified by the given user ID.
        Otherwise identical to :http:get:`/api/orders`.
        """
        return Order.query.filter(Order.ordered_by_id == user_id)

    def post(self, user_id):
        """
        Create a new order. The ordered_by_id parameter is implicitly set by
        the user_id given in the URL, and cannot be overridden by form
        parameters. Otherwise, identical to :http:post:`/api/orders`.
        """
        args = user_order_parser.parse_args()
        args['ordered_by_id'] = user_id
        order = Order.create(**args)
        db.session.add(order)
        db.session.commit()
        location = url_for('orderdetail', order_id=order.id)
        return {"message": "created", "id": order.id}, 201, {"Location": location}


@handle_sqlalchemy_errors
class OrganizationOrderList(Resource):
    model = Order

    @resource_list(Order, mfields)
    def get(self, org_id):
        """
        Get all orders placed by users in the organization identified by
        the given organization ID. Otherwise identical to :http:get:`/api/orders`.
        """
        return (Order.query
            .join(User)
            .filter(User.organization_id == org_id)
        )


@handle_sqlalchemy_errors
class OrganizationOrderListForDate(Resource):
    model = Order

    @resource_list(Order, mfields)
    def get(self, org_id, for_date):
        """
        Get all orders placed on the given date by users in the organization
        identified by the given organization ID. Otherwise identical to
        :http:get:`/api/orders`.
        """
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
