import json
import pytest
from seamless_karma.extensions import db
from factories import UserFactory, OrderFactory, VendorFactory
from six.moves.urllib.parse import urlparse


def test_empty(client):
    response = client.get('/api/orders')
    assert response.status_code == 200
    obj = json.loads(response.data)
    assert obj['count'] == 0


@pytest.fixture
def orders(app):
    o1 = OrderFactory.create()
    o2 = OrderFactory.create()
    db.session.commit()
    return [o1, o2]


def test_existing(client, orders):
    response = client.get('/api/orders')
    assert response.status_code == 200
    obj = json.loads(response.data)
    assert obj['count'] == len(orders)
    assert obj['data'][0]['ordered_by'] == orders[0].ordered_by_id
    assert (obj['data'][1]['contributions'][0]['amount'] ==
            str(orders[1].contributions[0].amount))


def test_create_no_args(client):
    response = client.post('/api/orders')
    assert response.status_code == 400
    obj = json.loads(response.data)
    err = ("at least one pair of contributed_by and contributed_amount"
           " values is required")
    assert err == obj['message']


def test_create(client):
    user = UserFactory.create()
    vendor = VendorFactory.create()
    db.session.commit()
    response = client.post('/api/orders', data={
        "contributed_by": user.id,
        "contributed_amount": "8.50",
        "ordered_by_id": user.id,
        "vendor_id": vendor.id,
    })
    assert response.status_code == 201
    assert "Location" in response.headers
    obj = json.loads(response.data)
    assert "id" in obj
    url = response.headers["Location"]
    path = urlparse(url).path
    resp2 = client.get(path)
    assert resp2.status_code == 200
    created = json.loads(resp2.data)
    assert created["contributions"][0]["amount"] == "8.50"
