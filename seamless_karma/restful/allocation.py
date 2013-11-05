from seamless_karma import app, db, api, models
from seamless_karma.models import User, Order
import sqlalchemy as sa
import six
from flask.ext.restful import Resource, abort, fields, marshal_with
from datetime import datetime, date
from decimal import Decimal
from . import TwoDecimalPlaceField, date_type
from .decorators import handle_sqlalchemy_errors


class OrganizationUnallocatedForDate(Resource):
    method_decorators = [handle_sqlalchemy_errors]

    def get(self, org_id, date_str):
        try:
            for_date = date_type(date_str, "date")
        except ValueError:
            abort(400, message="invalid date: {!r}".format(date_str))

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
        ret = {
            "total_unallocated": six.text_type(total),
            "data": [],
        }
        for user, unallocated, karma in main_query:
            ret["data"].append({
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "unallocated": six.text_type(unallocated),
                "karma": six.text_type(karma),
            })
        return ret


api.add_resource(OrganizationUnallocatedForDate,
    "/organizations/<int:org_id>/orders/<date_str>/unallocated")
