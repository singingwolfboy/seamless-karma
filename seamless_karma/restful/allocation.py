from seamless_karma.extensions import db, api
from seamless_karma.models import User
import sqlalchemy as sa
from flask import request
import six
from flask.ext.restful import Resource
from decimal import Decimal
from .decorators import handle_sqlalchemy_errors
from .utils import bool_from_str


@handle_sqlalchemy_errors
class OrganizationUnallocatedForDate(Resource):
    def get(self, org_id, for_date):
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
