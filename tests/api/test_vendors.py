# coding=utf-8
from __future__ import unicode_literals

import json
import pytest
from seamless_karma.extensions import db
from seamless_karma.models import Vendor
from factories import VendorFactory
from six.moves.urllib.parse import urlparse


def test_empty(client):
    response = client.get('/api/vendors')
    assert response.status_code == 200
    obj = json.loads(response.get_data(as_text=True))
    assert obj['count'] == 0


@pytest.fixture
def vendors(app):
    v1 = VendorFactory.create()
    v2 = VendorFactory.create()
    db.session.commit()
    return [v1, v2]


def test_existing(client, vendors):
    response = client.get('/api/vendors')
    assert response.status_code == 200
    obj = json.loads(response.get_data(as_text=True))
    assert obj['count'] == len(vendors)
    assert obj['data'][0]['name'] == str(vendors[0].name)


def test_create_no_args(client):
    response = client.post('/api/vendors')
    assert response.status_code == 400
    obj = json.loads(response.get_data(as_text=True))
    assert "Missing required parameter" in obj['message']


def test_create(client):
    response = client.post('/api/vendors', data={
        "name": "India Palace"
    })
    assert response.status_code == 201
    assert "Location" in response.headers
    obj = json.loads(response.get_data(as_text=True))
    assert "id" in obj
    url = response.headers["Location"]
    path = urlparse(url).path
    resp2 = client.get(path)
    assert resp2.status_code == 200
    created = json.loads(resp2.get_data(as_text=True))
    assert created["name"] == "India Palace"


def test_update_partial(client, vendors):
    vid = vendors[0].id
    url = "/api/vendors/{id}".format(id=vid)
    response = client.put(url, data={
        "name": "Back Bay Café",
    })
    assert response.status_code == 200
    obj = json.loads(response.get_data(as_text=True))
    assert obj["id"] == vid
    assert obj["name"] == "Back Bay Café"
    vendor = Vendor.query.get(vid)
    assert vendor.name == "Back Bay Café"
