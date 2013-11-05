from seamless_karma import app, db, api, models
from seamless_karma.models import User, Order
import sqlalchemy as sa
from flask.ext.restful import Resource, abort, fields, marshal_with
from datetime import datetime, date
from . import TwoDecimalPlaceField, date_type
from .decorators import handle_sqlalchemy_errors


class OrganizationUnallocatedForDate(Resource):
    method_decorators = [handle_sqlalchemy_errors]

    def get(self, org_id, date_str):
        try:
            for_date = date_type(date_str, "date")
        except ValueError:
            abort(400, message="invalid date: {!r}".format(date_str))
        # This ends up making *way* too many database calls, but I'll
        # optimize it later.
        users = (User.query
            .filter(User.organization_id == org_id)
            .order_by(sa.desc(User.unallocated(for_date)), User.karma)
            .all()
        )
        ret = []
        for user in users:
            ret.append({
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "karma": str(user.karma),  # another query: ouch!
                "unallocated": str(user.unallocated(for_date)), # another query: OUCH!
            })
        return ret


api.add_resource(OrganizationUnallocatedForDate,
    "/organizations/<int:org_id>/orders/<date_str>/unallocated")
