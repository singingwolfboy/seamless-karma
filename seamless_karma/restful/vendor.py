# coding=utf-8
from __future__ import unicode_literals

from seamless_karma.models import Vendor
from seamless_karma.extensions import db, api
from flask import url_for
from flask.ext.restful import Resource, abort, fields, marshal_with, reqparse
from decimal import Decimal
from .utils import make_optional
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


@handle_sqlalchemy_errors
class VendorList(Resource):
    model = Vendor

    @resource_list(Vendor, mfields, parser=make_optional(parser))
    def get(self):
        """
        Return a list of all vendors.

        Example response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
              "count": 3,
              "data": [
                {
                  "id": 1,
                  "seamless_id": 2345,
                  "name": "China Palace",
                  "latitude": null,
                  "longitude": null
                }, {
                  "id": 2,
                  "seamless_id": 569452,
                  "name": "Ponzu",
                  "latitude": 14.003424,
                  "longitude": 284.342345
                }, {
                  "id": 3,
                  "seamless_id": null,
                  "name": "Bob's Steakhouse",
                  "latitude": -83.230234,
                  "longitude": 320.432534
                }
              ]
            }
        """
        return Vendor.query

    def post(self):
        """
        Create a new vendor (restaurant).

        :form name: *Required* The name of the vendor on Seamless_
        :form seamless_id: *Optional* The ID of the vendor on Seamless_
        :form latitude: *Optional* The latitude corresponding to the vendor's
            location
        :form longitude: *Optional* The longitude corresponding to the vendor's
            location

        Example response:

        .. sourcecode:: http

            HTTP/1.1 201 CREATED
            Content-Type: application/json
            Location: /api/vendors/7

            {
              "message": "created",
              "id": 7
            }

        :status 201: the vendor was successfully created

        .. _Seamless: http://www.seamless.com
        """
        args = parser.parse_args()
        vendor = Vendor(**args)
        db.session.add(vendor)
        db.session.commit()
        location = url_for('vendordetail', vendor_id=vendor.id)
        return {"message": "created", "id": vendor.id}, 201, {"Location": location}


@handle_sqlalchemy_errors
class VendorDetail(Resource):
    model = Vendor

    def get_vendor_or_abort(self, id):
        vendor = Vendor.query.get(id)
        if not vendor:
            abort(404, message="Vendor {} does not exist".format(id))
        return vendor

    @marshal_with(mfields)
    def get(self, vendor_id):
        """
        Return information about a specific vendor, identified by ID.

        Example response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
              "id": 93,
              "seamless_id": 230934,
              "name": "Bob's Diner",
              "latitude": 83.23834,
              "longitude": -23.340924
            }

        :status 200: no error
        :status 404: there is no vendor with the given ID
        """
        return self.get_vendor_or_abort(vendor_id)

    @marshal_with(mfields)
    def put(self, vendor_id):
        """
        Update information about a specific vendor, identified by ID.

        Example request:

        .. sourcecode:: http

            PUT /api/vendors/12 HTTP/1.1
            Host: seamlesskarma.com
            Content-Type: application/x-www-form-urlencoded
            Content-Length: 17

            seamless_id=9

        Example response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
              "id": 12,
              "seamless_id": 9,
              "name": "Bob's Wings",
              "latitude": null,
              "longitude": null
            }

        :form seamless_id: *Optional* updated Seamless ID
        :form name: *Optional* updated name
        :form latitude: *Optional* updated latitude
        :form longitude: *Optional* updated longitude
        :status 200: the vendor was updated
        :status 404: there is no vendor with the given ID
        """
        vendor = self.get_vendor_or_abort(vendor_id)
        args = make_optional(parser).parse_args()
        for attr in ('seamless_id', 'name', 'latitude', 'longitude'):
            if attr in args:
                setattr(vendor, attr, args[attr])
        db.session.add(vendor)
        db.session.commit()
        return vendor

    def delete(self, vendor_id):
        """
        Delete a specific vendor, identified by ID.

        Example response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
              "message": "deleted"
            }

        :status 200: the vendor was deleted
        :status 404: there is no vendor with the given ID
        """
        vendor = self.get_vendor_or_abort(vendor_id)
        db.session.delete(vendor)
        db.session.commit()
        return {"message": "deleted"}, 200


api.add_resource(VendorList, "/vendors")
api.add_resource(VendorDetail, "/vendors/<int:vendor_id>")
