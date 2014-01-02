import json
import pytest
from seamless_karma.extensions import db
from seamless_karma.models import User
from factories import UserFactory, OrderFactory, OrganizationFactory, VendorFactory
from six.moves.urllib.parse import urlparse


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
    obj = json.loads(response.data)
    assert obj['data'] == []


@pytest.fixture
def users(app, org):
    u1 = UserFactory.create(organization=org)
    u2 = UserFactory.create(organization=org)
    db.session.commit()
    return [u1, u2]


def test_empty_with_users(client, org, users):
    url = "/api/organizations/{org_id}/orders/2014-01-01/unallocated".format(
        org_id=org.id)
    response = client.get(url)
    assert response.status_code == 200
    obj = json.loads(response.data)
    assert obj['data'] == []


def test_empty_with_users_display_nonparticipants(client, org, users):
    url = ("/api/organizations/{org_id}/orders/2014-01-01/unallocated"
           "?nonparticipants=true".format(org_id=org.id))
    response = client.get(url)
    assert response.status_code == 200
    obj = json.loads(response.data)
    assert len(obj['data']) == len(users)
