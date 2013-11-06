from seamless_karma import app, db, api, models
from flask import request, url_for
from flask.ext.restful import Resource, abort, fields, marshal_with, reqparse
from decimal import Decimal
from .utils import TwoDecimalPlaceField, string_or_int_type, make_optional
from .decorators import handle_sqlalchemy_errors, resource_list


mfields = {
    "id": fields.Integer,
    "username": fields.String,
    "first_name": fields.String,
    "last_name": fields.String,
    "allocation": TwoDecimalPlaceField,
    "karma": TwoDecimalPlaceField,
    "organization": fields.Integer(attribute="organization_id"),
    # "organization": fields.Nested({
    #     "id": fields.Integer,
    #     "name": fields.String,
    # }),
}

parser = reqparse.RequestParser()
parser.add_argument('username', required=True)
parser.add_argument('organization', type=string_or_int_type, required=True)
parser.add_argument('first_name', required=True)
parser.add_argument('last_name', required=True)
parser.add_argument('allocation', type=Decimal,
    help="Seamless allocation of user, as a decimal string")

class UserList(Resource):
    method_decorators = [handle_sqlalchemy_errors]

    @resource_list(models.User, mfields)
    def get(self):
        return models.User.query

    def get_or_create_org(self, args):
        if isinstance(args["organization"], int):
            org = models.Organization.query.get(args["organization"])
            if not org:
                abort(400, message="invalid organization ID")
            return org

        # we have a string, so it must be the org name
        org = models.Organization.query.filter_by(name=args["organization"]).first()
        if not org:
            # we can dynamically create it if we have an allocation value
            if not args.get("allocation"):
                abort(400, message="organization does not exist; "
                    "cannot create without allocation value")
            org = models.Organization(
                name=args["organization"],
                default_allocation=args["allocation"],
            )
            db.session.add(org)

        return org

    def post(self):
        args = parser.parse_args()
        org = self.get_or_create_org(args)
        args['organization'] = org
        user = models.User(**args)
        db.session.add(user)
        db.session.commit()
        location = url_for('user', user_id=user.id)
        return {"message": "created"}, 201, {"Location": location}


class User(Resource):
    method_decorators = [handle_sqlalchemy_errors]

    def get_user_or_abort(self, id):
        u = models.User.query.get(id)
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
        for attr in ('username', 'first_name', 'last_name', 'allocation'):
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

api.add_resource(UserList, "/users")
api.add_resource(User, "/users/<int:user_id>")
