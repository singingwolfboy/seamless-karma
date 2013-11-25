from seamless_karma.models import db, Organization
from seamless_karma.extensions import api
import sqlalchemy as sa
from flask import request, url_for
from flask.ext.restful import Resource, abort, fields, marshal_with, reqparse
from decimal import Decimal
from .utils import TwoDecimalPlaceField
from .decorators import handle_sqlalchemy_errors, resource_list

mfields = {
    "id": fields.Integer,
    "seamless_id": fields.Integer(default=None),
    "name": fields.String,
    "default_allocation": TwoDecimalPlaceField,
}

parser = reqparse.RequestParser()
parser.add_argument('seamless_id', type=int)
parser.add_argument('name')
parser.add_argument('default_allocation', type=Decimal)

class OrganizationList(Resource):
    method_decorators = [handle_sqlalchemy_errors]

    @resource_list(Organization, mfields)
    def get(self):
        return Organization.query

    def post(self):
        args = parser.parse_args()
        org = Organization(**args)
        db.session.add(org)
        db.session.commit()
        location = url_for('organization', org_id=org.id)
        return {"message": "created", "id": "org.id"}, 201, {"Location": location}


class OrganizationDetail(Resource):
    method_decorators = [handle_sqlalchemy_errors]

    def get_org_or_abort(self, id):
        o = Organization.query.get(id)
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
        for attr in ('seamless_id', 'name', 'default_allocation'):
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


class OrganizationByName(Resource):
    method_decorators = [handle_sqlalchemy_errors]

    def get_org_or_abort(self, name):
        try:
            return (Organization.query
                    .filter(Organization.name == name)
                    .one()
            )
        except sa.orm.exc.NoResultFound:
            abort(404, message="Organization {} does not exist".format(username))

    @marshal_with(mfields)
    def get(self, name):
        return self.get_org_or_abort(name)

    @marshal_with(mfields)
    def put(self, name):
        o = self.get_org_or_abort(name)
        args = make_optional(parser).parse_args()
        for attr in ('seamless_id', 'default_allocation'):
            if attr in args:
                setattr(o, attr, args[attr])
        db.session.add(o)
        db.session.commit()
        return o

    def delete(self, name):
        o = self.get_org_or_abort(name)
        db.session.delete(o)
        db.session.commit()
        return {"message": "deleted"}, 200


api.add_resource(OrganizationList, "/organizations")
api.add_resource(OrganizationDetail, "/organizations/<int:org_id>")
api.add_resource(OrganizationByName, "/organizations/<name>")
