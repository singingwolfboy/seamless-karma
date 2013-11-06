from seamless_karma import app, db, api, models
from flask import request, url_for
from flask.ext.restful import Resource, abort, fields, marshal_with, reqparse
from decimal import Decimal
from .utils import TwoDecimalPlaceField, paginate_query
from .decorators import handle_sqlalchemy_errors, resource_list

mfields = {
    "id": fields.Integer,
    "name": fields.String,
    "default_allocation": TwoDecimalPlaceField,
}

parser = reqparse.RequestParser()
parser.add_argument('name')
parser.add_argument('default_allocation', type=Decimal)

class OrganizationList(Resource):
    method_decorators = [handle_sqlalchemy_errors]

    @resource_list(models.Organization, mfields)
    def get(self):
        return models.Organization.query

    def post(self):
        args = parser.parse_args()
        org = models.Organization(**args)
        db.session.add(org)
        db.session.commit()
        location = url_for('organization', org_id=org.id)
        return {"message": "created"}, 201, {"Location": location}


class Organization(Resource):
    method_decorators = [handle_sqlalchemy_errors]

    def get_org_or_abort(self, id):
        o = models.Organization.query.get(id)
        if not o:
            abort(404, message="Organization {} does not exist".format(id))
        return o

    @marshal_with(mfields)
    def get(self, org_id):
        return self.get_org_or_abort(org_id)

    @marshal_with(mfields)
    def put(self, org_id):
        o = self.get_org_or_abort(org_id)
        args = make_optional(parser).parse_args()
        for attr in ('name', 'default_allocation'):
            if attr in args:
                setattr(o, attr, args[attr])
        db.session.add(o)
        db.session.commit()
        return o

    def delete(self, org_id):
        o = self.get_org_or_abort(org_id)
        db.session.delete(o)
        db.session.commit()
        return {"message": "deleted"}, 200


api.add_resource(OrganizationList, "/organizations")
api.add_resource(Organization, "/organizations/<int:org_id>")
