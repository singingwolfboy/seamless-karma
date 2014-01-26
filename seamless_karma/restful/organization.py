from seamless_karma.models import Organization
from seamless_karma.extensions import db, api
import sqlalchemy as sa
from flask import url_for
from flask.ext.restful import Resource, abort, fields, marshal_with, reqparse
from decimal import Decimal
from .utils import TwoDecimalPlaceField, make_optional
from .decorators import handle_sqlalchemy_errors, resource_list

mfields = {
    "id": fields.Integer,
    "seamless_id": fields.Integer(default=None),
    "name": fields.String,
    "default_allocation": TwoDecimalPlaceField,
}

parser = reqparse.RequestParser()
parser.add_argument('seamless_id', type=int)
parser.add_argument('name', required=True)
parser.add_argument('default_allocation', type=Decimal)


@handle_sqlalchemy_errors
class OrganizationList(Resource):
    model = Organization

    @resource_list(Organization, mfields, parser=make_optional(parser))
    def get(self):
        """
        Return a list of all organizations.

        Example response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
              "count": 2,
              "data": [
                {
                  "id": 1,
                  "seamless_id": 34235,
                  "name": "edX",
                  "default_allocation": "11.50"
                }, {
                  "id": 2,
                  "seamless_id": 23443,
                  "name": "Twitter",
                  "default_allocation": null
                }
              ]
            }
        """
        return Organization.query

    def post(self):
        """
        Create a new organization.

        :form name: *Required* The name of the organization on Seamless_
        :form seamless_id: *Optional* The ID of this organization on Seamless_
        :form default_allocation: *Optional* The default allocation to assign
            to new users in this organization.

        Example request:

        .. sourcecode:: http

            POST /api/organizations HTTP/1.1
            Host: seamlesskarma.com
            Content-Type: application/x-www-form-urlencoded
            Content-Length: 51

            seamless_id=523&name=foobie&default_allocation=9.75

        Example response:

        .. sourcecode:: http

            HTTP/1.1 201 CREATED
            Content-Type: application/json
            Location: /api/organizations/8

            {
              "message": "created",
              "id": 8
            }

        :status 201: the organization was successfully created
        :status 400: invalid or insufficient information to create
            the organization

        .. _Seamless: http://www.seamless.com
        """
        args = parser.parse_args()
        org = Organization(**args)
        db.session.add(org)
        db.session.commit()
        location = url_for('organizationdetail', org_id=org.id)
        return {"message": "created", "id": org.id}, 201, {"Location": location}


@handle_sqlalchemy_errors
class OrganizationDetail(Resource):
    model = Organization

    def get_org_or_abort(self, id):
        o = Organization.query.get(id)
        if not o:
            abort(404, message="Organization {} does not exist".format(id))
        return o

    @marshal_with(mfields)
    def get(self, org_id):
        """
        Return information about a specific organization, identified by ID.

        Example response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
              "id": 1,
              "seamless_id": 742934,
              "name": "edX",
              "default_allocation": "11.50"
            }

        :status 200: no error
        :status 404: there is no user with the given ID
        """
        return self.get_org_or_abort(org_id)

    @marshal_with(mfields)
    def put(self, org_id):
        """
        Update information about a specific organization, identified by ID.

        Example request:

        .. sourcecode:: http

            PUT /api/organizations/1 HTTP/1.1
            Host: seamlesskarma.com
            Content-Type: application/x-www-form-urlencoded
            Content-Length: 40

            seamless_id=888&default_allocation=42.00

        Example response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
              "id": 1,
              "seamless_id": 888,
              "name": "edX",
              "default_allocation": "42.00"
            }

        :form seamless_id: *Optional* updated Seamless ID
        :form name: *Optional* updated name
        :form default_allocation: *Optional* updated default allocation
        :status 200: the organization was updated
        :status 404: there is no organization with the given ID
        """
        o = self.get_org_or_abort(org_id)
        args = make_optional(parser).parse_args()
        for attr in ('seamless_id', 'name', 'default_allocation'):
            if attr in args:
                setattr(o, attr, args[attr])
        db.session.add(o)
        db.session.commit()
        return o

    def delete(self, org_id):
        """
        Delete a specific organization, identified by ID.

        Example response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
              "message": "deleted"
            }

        :status 200: the organization was deleted
        :status 404: there is no organization with the given ID
        """
        o = self.get_org_or_abort(org_id)
        db.session.delete(o)
        db.session.commit()
        return {"message": "deleted"}, 200


@handle_sqlalchemy_errors
class OrganizationByName(Resource):
    model = Organization

    def get_org_or_abort(self, name):
        try:
            return Organization.query.filter(Organization.name == name).one()
        except sa.orm.exc.NoResultFound:
            abort(404, message="Organization {} does not exist".format(name))

    @marshal_with(mfields)
    def get(self, name):
        """
        Get a specific organization, identified by name. Otherwise identical
        to :http:get:`/api/organizations/(id:org_id)`
        """
        return self.get_org_or_abort(name)

    @marshal_with(mfields)
    def put(self, name):
        """
        Update a specific organization, identified by name. Cannot update
        organization name. Otherwise identical to
        :http:put:`/api/organizations/(id:org_id)`
        """
        o = self.get_org_or_abort(name)
        args = make_optional(parser).parse_args()
        for attr in ('seamless_id', 'default_allocation'):
            if attr in args:
                setattr(o, attr, args[attr])
        db.session.add(o)
        db.session.commit()
        return o

    def delete(self, name):
        """
        Delete a specific organization, identified by name. Otherwise identical
        to :http:delete:`/api/organizations(id:org_id)`
        """
        o = self.get_org_or_abort(name)
        db.session.delete(o)
        db.session.commit()
        return {"message": "deleted"}, 200


api.add_resource(OrganizationList, "/organizations")
api.add_resource(OrganizationDetail, "/organizations/<int:org_id>")
api.add_resource(OrganizationByName, "/organizations/<name>")
