from seamless_karma.models import User, Organization
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
    "username": fields.String,
    "first_name": fields.String,
    "last_name": fields.String,
    "allocation": TwoDecimalPlaceField,
    "karma": TwoDecimalPlaceField,
    "organization_id": fields.Integer,
    # "organization": fields.Nested({
    #     "id": fields.Integer,
    #     "name": fields.String,
    # }),
}

parser = reqparse.RequestParser()
parser.add_argument('seamless_id', type=int)
parser.add_argument('username', required=True)
parser.add_argument('organization')  # one of org or org_id is required
parser.add_argument('organization_id', type=int)
parser.add_argument('first_name', required=True)
parser.add_argument('last_name', required=True)
parser.add_argument('allocation', type=Decimal,
    help="Seamless allocation of user, as a decimal string")


class UserList(Resource):
    model = User
    method_decorators = [handle_sqlalchemy_errors]

    @resource_list(User, mfields, parser=make_optional(parser))
    def get(self):
        """
        Return a list of all users.

        Example response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
              "count": 3,
              "data": [
                {
                  "id": 1,
                  "seamless_id": 342534,
                  "username": "ASample",
                  "organization_id": 1,
                  "first_name": "Alice",
                  "last_name": "Sample",
                  "allocation": "11.50",
                  "karma": "21.00"
                }, {
                  "id": 2,
                  "seamless_id": 234013,
                  "username": "GRipple2",
                  "organization_id": 1,
                  "first_name": "Greg",
                  "last_name": "Ripple",
                  "allocation": "11.50",
                  "karma": "0.00"
                }, {
                  "id": 4,
                  "seamless_id": null,
                  "username": "iDontKnow",
                  "organization_id": 2,
                  "first_name": "Samantha",
                  "last_name": "Smith",
                  "allocation": "21.20",
                  "karma": "-3.20"
                }
              ]
            }
        """
        return self.model.query

    def get_or_create_org(self, args):
        if args.get("organization_id") is not None:
            org = Organization.query.get(args["organization_id"])
            if not org:
                abort(400, message="invalid organization ID")
            return org

        if args.get("organization") is not None:
            org_name = args["organization"]
            org = Organization.query.filter_by(name=org_name).first()
            if not org:
                # we can dynamically create it if we have an allocation value
                if not args.get("allocation"):
                    abort(400, message="organization does not exist; "
                        "cannot create without allocation value")
                org = Organization(
                    name=org_name,
                    default_allocation=args["allocation"],
                )
                db.session.add(org)

            return org

        abort(400, message="one of `organization` or `organization_id` is required")

    def post(self):
        """
        Create a new user.

        :form username: *Required* The username of the user on Seamless_
        :form seamless_id: *Optional* The ID of the user on Seamless_
        :form first_name: *Required* The user's first name, as saved on Seamless_
        :form last_name: *Required* The user's last name, as saved on Seamless_
        :form organization: You must specify what organization this user belongs
            to on Seamless_. You can do this in one of several ways. If the
            organization already exists on SeamlessKarma, you may either pass
            the ID of the organization with the ``organization_id`` form parameter,
            or the name of the organization with the ``organization`` form
            parameter. If the organization does not yet exist on SeamlessKarma,
            you can create it as part of this API call by specifying the name
            with the ``organization`` form parameter, and also specifying the
            ``allocation`` form parameter.
        :form organization_id: Either this or ``organization`` is required, but
            not both.
        :form allocation: The user's daily allocation on Seamless_ in dollars.
            For example, "11.50". If you are also creating an organization with
            this API call, this form parameter is required; the value will be
            used not only as this user's daily allocation, but also as the
            default allocation for the newly-created organization. If you are
            not creating an organization with this API call, this form parameter
            is optional; it will default to the default allocation of this
            user's organization.

        Example response:

        .. sourcecode:: http

            HTTP/1.1 201 CREATED
            Content-Type: application/json
            Location: /api/users/7

            {
              "message": "created",
              "id" 7
            }

        :status 201: the user was successfully created

        .. _Seamless: http://www.seamless.com
        """
        args = parser.parse_args()
        org = self.get_or_create_org(args)
        if "organization_id" in args:
            del args["organization_id"]
        args['organization'] = org
        user = User.create(**args)
        db.session.add(user)
        if user.allocation is None:
            abort(400, message="allocation is required in values "
                "(organization has no default allocation set)")
        db.session.commit()
        location = url_for('userdetail', user_id=user.id)
        return {"message": "created", "id": user.id}, 201, {"Location": location}


class UserDetail(Resource):
    model = User
    method_decorators = [handle_sqlalchemy_errors]

    def get_user_or_abort(self, id):
        u = User.query.get(id)
        if not u:
            abort(404, message="User {} does not exist".format(id))
        return u

    @marshal_with(mfields)
    def get(self, user_id):
        """
        Return information about a specific user, identified by ID.

        Example response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
              "id": 42,
              "seamless_id": 742934,
              "username": "SBrown",
              "first_name": "Sally",
              "last_name": "Brown",
              "allocation": "11.50",
              "karma": "-27.45",
              "organization_id": 3
            }

        :status 200: no error
        :status 404: there is no user with the given ID
        """
        return self.get_user_or_abort(user_id)

    @marshal_with(mfields)
    def put(self, user_id):
        """
        Update information about a specific user, identified by ID.

        Example request:

        .. sourcecode:: http

            PUT /api/users/42 HTTP/1.1
            Host: seamlesskarma.com
            Content-Type: application/x-www-form-urlencoded
            Content-Length: 17

            seamless_id=12345

        Example response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
              "id": 42,
              "seamless_id": 12345,
              "username": "SBrown",
              "first_name": "Sally",
              "last_name": "Brown",
              "allocation": "11.50",
              "karma": "-27.45",
              "organization_id": 3
            }

        :form seamless_id: *Optional* updated Seamless ID
        :form username: *Optional* updated Seamless username
        :form first_name: *Optional* updated first name
        :form last_name: *Optional* updated allocation
        :status 200: the user was updated
        :status 404: there is no user with the given ID
        """
        u = self.get_user_or_abort(user_id)
        args = make_optional(parser).parse_args()
        for attr in ('seamless_id', 'username', 'first_name', 'last_name', 'allocation'):
            if attr in args:
                setattr(u, attr, args[attr])
        db.session.add(u)
        db.session.commit()
        return u

    def delete(self, user_id):
        """
        Delete a specific user, identified by ID.

        Example response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
              "message": "deleted"
            }

        :status 200: the user was deleted
        :status 404: there is no user with the given ID
        """
        u = self.get_user_or_abort(user_id)
        db.session.delete(u)
        db.session.commit()
        return {"message": "deleted"}, 200


class UserByUsername(Resource):
    model = User
    method_decorators = [handle_sqlalchemy_errors]

    def get_user_or_abort(self, username):
        try:
            return User.query.filter(User.username == username).one()
        except sa.orm.exc.NoResultFound:
            abort(404, message="User with username {} does not exist".format(username))

    @marshal_with(mfields)
    def get(self, username):
        """
        Get a user by Seamless username instead of by ID. Otherwise identical
        to :http:get:`/api/users/(int:user_id)`
        """
        return self.get_user_or_abort(username)

    @marshal_with(mfields)
    def put(self, username):
        """
        Update a user by Seamless username instead of by ID. Cannot update
        Seamless username. Otherwise identical to
        :http:put:`/api/users/(int:user_id)`.
        """
        u = self.get_user_or_abort(username)
        args = make_optional(parser).parse_args()
        for attr in ('seamless_id', 'first_name', 'last_name', 'allocation'):
            if attr in args:
                setattr(u, attr, args[attr])
        db.session.add(u)
        db.session.commit()
        return u

    def delete(self, username):
        """
        Delete a user by Seamless username instead of by ID. Otherwise
        identical to :http:delete:`/api/users/(int:user_id)`.
        """
        u = self.get_user_or_abort(username)
        db.session.delete(u)
        db.session.commit()
        return {"message": "deleted"}, 200

api.add_resource(UserList, "/users")
api.add_resource(UserDetail, "/users/<int:user_id>")
api.add_resource(UserByUsername, "/users/<username>")
