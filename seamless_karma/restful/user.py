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
    method_decorators = [handle_sqlalchemy_errors]

    @resource_list(User, mfields, parser=make_optional(parser))
    def get(self):
        return User.query

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
    method_decorators = [handle_sqlalchemy_errors]

    def get_user_or_abort(self, id):
        u = User.query.get(id)
        if not u:
            abort(404, message="User {} does not exist".format(id))
        return u

    @marshal_with(mfields)
    def get(self, user_id):
        return self.get_user_or_abort(user_id)

    @marshal_with(mfields)
    def put(self, user_id):
        u = self.get_user_or_abort(user_id)
        args = make_optional(parser).parse_args()
        for attr in ('seamless_id', 'username', 'first_name', 'last_name', 'allocation'):
            if attr in args:
                setattr(u, attr, args[attr])
        db.session.add(u)
        db.session.commit()
        return u

    def delete(self, user_id):
        u = self.get_user_or_abort(user_id)
        db.session.delete(u)
        db.session.commit()
        return {"message": "deleted"}, 200


class UserByUsername(Resource):
    method_decorators = [handle_sqlalchemy_errors]

    def get_user_or_abort(self, username):
        try:
            return User.query.filter(User.username == username).one()
        except sa.orm.exc.NoResultFound:
            abort(404, message="User with username {} does not exist".format(username))

    @marshal_with(mfields)
    def get(self, username):
        return self.get_user_or_abort(username)

    @marshal_with(mfields)
    def put(self, username):
        u = self.get_user_or_abort(username)
        args = make_optional(parser).parse_args()
        for attr in ('seamless_id', 'first_name', 'last_name', 'allocation'):
            if attr in args:
                setattr(u, attr, args[attr])
        db.session.add(u)
        db.session.commit()
        return u

    def delete(self, username):
        u = self.get_user_or_abort(username)
        db.session.delete(u)
        db.session.commit()
        return {"message": "deleted"}, 200

api.add_resource(UserList, "/users")
api.add_resource(UserDetail, "/users/<int:user_id>")
api.add_resource(UserByUsername, "/users/<username>")
