from seamless_karma import app, db, api, models
from flask import request, url_for
from flask.ext.restful import Resource, abort, fields, marshal_with, reqparse
from decimal import Decimal
from .utils import TwoDecimalPlaceField
from .decorators import handle_sqlalchemy_errors, resource_list

mfields = {
    "id": fields.Integer,
    "seamless_id": fields.Integer(default=None),
    "latitude": fields.Arbitrary(default=None),
    "longitute": fields.Arbitrary(default=None),
    "name": fields.String,
}

parser = reqparse.RequestParser()
parser.add_argument('name', required=True)
parser.add_argument('seamless_id', type=int)
parser.add_argument('latitude', type=Decimal)
parser.add_argument('longitude', type=Decimal)

class VendorList(Resource):
    method_decorators = [handle_sqlalchemy_errors]

    @resource_list(models.Vendor, mfields)
    def get(self):
        return models.Vendor.query

    def post(self):
        args = parser.parse_args()
        vendor = models.Vendor(**args)
        db.session.add(vendor)
        db.session.commit()
        location = url_for('vendor', vendor_id=vendor.id)
        return {"message": "created", "id": vendor.id}, 201, {"Location": location}


class Vendor(Resource):
    method_decorators = [handle_sqlalchemy_errors]

    def get_vendor_or_abort(self, id):
        vendor = models.Vendor.query.get(id)
        if not vendor:
            abort(404, message="Vendor {} does not exist".format(id))
        return vendor

    @marshal_with(mfields)
    def get(self, vendor_id):
        return self.get_vendor_or_abort(vendor_id)

    @marshal_with(mfields)
    def put(self, vendor_id):
        vendor = self.get_vendor_or_abort(vendor_id)
        args = make_optional(parser).parse_args()
        for attr in ('seamless_id', 'name', 'latitude', 'longitude'):
            if attr in args:
                setattr(vendor, attr, args[attr])
        db.session.add(vendor)
        db.session.commit()
        return vendor

    def delete(self, vendor_id):
        vendor = self.get_vendor_or_abort(vendor_id)
        db.session.delete(vendor)
        db.session.commit()
        return {"message": "deleted"}, 200


api.add_resource(VendorList, "/vendors")
api.add_resource(Vendor, "/vendors/<int:vendor_id>")
