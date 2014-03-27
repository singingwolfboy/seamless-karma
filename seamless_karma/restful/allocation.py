# coding=utf-8
from __future__ import unicode_literals

from seamless_karma.extensions import db, api
from seamless_karma.models import User
import sqlalchemy as sa
from flask import request
import six
from flask.ext.restful import Resource
from decimal import Decimal
from .decorators import cors, handle_sqlalchemy_errors
from .utils import bool_from_str


class OrganizationUnallocatedForDate(Resource):
    decorators = [cors, handle_sqlalchemy_errors()]

    def get(self, org_id, for_date):
        """
        Return information about unallocated Seamless money for the given date,
        for users within the organization identified by the given organization
        ID. This API is intended to be used by a Seamless user to determine
        which users can be added to his/her unplaced order. The information
        is sorted first by amount of unallocated money available, then by Karma
        rating (users with a low Karma are shown more prominently).

        By default, users are only returned from this API call if they have
        already participated in at least one order for the given date, indicating
        that they have already used whatever part of their allocation that they
        want for themselves. However, to display information about *all* users
        in the organization, whether they have participated in an order for that
        day or not, see the ``nonparticipants`` query parameter. Be nice: don't
        steal lunch money from others who want or need it!

        Example response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
              "total_unallocated": "15.10",
              "data": [
                {
                  "id": 1,
                  "first_name": "Frank",
                  "last_name": "Smith",
                  "unallocated": "5.20",
                  "karma": "8.20"
                }, {
                  "id": 93,
                  "first_name": "Sally",
                  "last_name": "Rivers",
                  "unallocated": "4.90",
                  "karma": "-3.20"
                }, {
                  "id": 43,
                  "first_name": "Alejandro",
                  "last_name": "Cortez",
                  "unallocated": "2.25",
                  "karma": "-4.90"
                }, {
                  "id": 23,
                  "first_name": "Silva",
                  "last_name": "Winters",
                  "unallocated": "2.25",
                  "karma": "0.40"
                }, {
                  "id": 81,
                  "first_name": "Brian",
                  "last_name": "Masters",
                  "unallocated": "0.50",
                  "karma": "9.20"
                }
              ]
            }

        :query nonparticipants: If set to `true`, this API call will return
            information about *all* users in the organization, regardless
            of whether they have participated in an order for the given day
            or not.
        :status 200: no errors
        """
        # are we including nonparticipants? (users in this org who have not yet
        # participated in an order for this date)
        nonparticipants = bool_from_str(request.args.get('nonparticipants', False))
        total_query = (db.session.query(
                sa.func.coalesce(
                    sa.func.sum(User.unallocated(for_date)),
                    Decimal('0.00')
                )
            )
            .filter(User.organization_id == org_id)
        )
        if not nonparticipants:
            total_query = total_query.filter(User.participated_on(for_date))
        total = total_query.scalar()

        main_query = (db.session.query(User, User.unallocated(for_date), User.karma)
            .filter(User.organization_id == org_id)
            .order_by(sa.desc(User.unallocated(for_date)), User.karma)
        )
        if not nonparticipants:
            main_query = main_query.filter(User.participated_on(for_date))

        output = {
            "total_unallocated": six.text_type(total),
            "data": [],
        }
        for user, unallocated, karma in main_query:
            output["data"].append({
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "unallocated": six.text_type(unallocated),
                "karma": six.text_type(karma),
            })
        return output


api.add_resource(
    OrganizationUnallocatedForDate,
    "/organizations/<int:org_id>/orders/<date:for_date>/unallocated"
)
