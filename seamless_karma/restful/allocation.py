from seamless_karma.extensions import db, api
from seamless_karma.models import User, Order
import sqlalchemy as sa
import six
from flask.ext.restful import Resource, abort, fields, marshal_with
from datetime import datetime, date
from decimal import Decimal
from .utils import TwoDecimalPlaceField, date_type
from .decorators import handle_sqlalchemy_errors


class OrganizationUnallocatedForDate(Resource):
    method_decorators = [handle_sqlalchemy_errors]

    def get(self, org_id, for_date):
        total = (db.session.query(
                sa.func.coalesce(
                    sa.func.sum(User.unallocated(for_date)),
                    Decimal('0.00')
                )
            )
            .filter(User.organization_id == org_id)
            .scalar()
        )
        main_query = (db.session.query(User, User.unallocated(for_date), User.karma)
            .filter(User.organization_id == org_id)
            .order_by(sa.desc(User.unallocated(for_date)), User.karma)
        )
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


api.add_resource(OrganizationUnallocatedForDate,
    "/organizations/<int:org_id>/orders/<date:for_date>/unallocated")
