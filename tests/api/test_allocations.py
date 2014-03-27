# coding=utf-8
from __future__ import unicode_literals

import json
import pytest
from decimal import Decimal
from seamless_karma.extensions import db
from factories import UserFactory, OrderFactory, OrganizationFactory


@pytest.fixture
def org(app):
    org = OrganizationFactory.create()
    db.session.commit()
    return org


def test_empty(client, org):
    url = "/api/organizations/{org_id}/orders/2014-01-01/unallocated".format(
        org_id=org.id)
    response = client.get(url)
    assert response.status_code == 200
    obj = json.loads(response.get_data(as_text=True))
    assert obj['data'] == []


@pytest.fixture
def users(app, org):
    u1 = UserFactory.create(organization=org, allocation=Decimal("10.00"))
    u2 = UserFactory.create(organization=org, allocation=Decimal("11.50"))
    db.session.commit()
    return [u1, u2]


def test_empty_with_users(client, org, users):
    url = "/api/organizations/{org_id}/orders/2014-01-01/unallocated".format(
        org_id=org.id)
    response = client.get(url)
    assert response.status_code == 200
    obj = json.loads(response.get_data(as_text=True))
    assert obj['data'] == []
    assert obj['total_unallocated'] == "0.00"


def test_empty_with_users_display_nonparticipants(client, org, users):
    url = (
        "/api/organizations/{org_id}/orders/2014-01-01/unallocated"
        "?nonparticipants=true".format(org_id=org.id)
    )
    response = client.get(url)
    assert response.status_code == 200
    obj = json.loads(response.get_data(as_text=True))
    assert len(obj['data']) == len(users)
    assert obj['total_unallocated'] == "21.50"


def test_one_order(client, users):
    # create an order
    order = OrderFactory.create(
        ordered_by=users[0],
        contributions=(
            (users[0], Decimal("5.00")),
            (users[1], Decimal("6.00")),
        )
    )
    db.session.add(order)
    db.session.commit()
    url = (
        "/api/organizations/{org_id}/orders/{date}/unallocated"
        "?nonparticipants=true".format(
            org_id=users[0].organization.id, date=order.for_date
        )
    )
    response = client.get(url)
    assert response.status_code == 200
    obj = json.loads(response.get_data(as_text=True))
    assert len(obj['data']) == len(users)
    assert obj['total_unallocated'] == "10.50"
