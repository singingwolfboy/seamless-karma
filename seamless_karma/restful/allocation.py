from seamless_karma import app, db, api, models
from seamless_karma.models import User, Order
from sqlalchemy import desc
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
        q = (db.session.query(
                User.id, User.first_name, User.last_name,
                User.karma.as_scalar(),
                User.unallocated(for_date).as_scalar(),
            )
            .filter(User.organization_id == org_id)
            .order_by(desc(User.unallocated(for_date)), User.karma)
            .all()
        )
        ret = []
        for id, first_name, last_name, karma, unallocated in q:
            ret.append(dict(id=id, first_name=first_name,
                last_name=last_name, karma=str(karma), unallocated=str(unallocated)))
        return ret


api.add_resource(OrganizationUnallocatedForDate,
    "/organizations/<int:org_id>/orders/<date_str>/unallocated")
