import json
import pytest
from seamless_karma.extensions import db
from seamless_karma.models import User
import factory
from six.moves.urllib.parse import urlparse

def test_empty(client):
    response = client.get('/api/organizations')
    assert response.status_code == 200
    obj = json.loads(response.data)
    assert obj['count'] == 0


@pytest.fixture
def orgs(app, OrganizationFactory):
    org1 = OrganizationFactory.create()
    org2 = OrganizationFactory.create(name="Coursera")
    db.session.commit()
    return [org1, org2]


def test_existing(client, orgs):
    response = client.get('/api/organizations')
    assert response.status_code == 200
    obj = json.loads(response.data)
    assert obj['count'] == len(orgs)
    assert obj['data'][0]['default_allocation'] == str(orgs[0].default_allocation)
    assert obj['data'][1]['name'] == orgs[1].name


def test_create_no_args(client):
    response = client.post('/api/organizations')
    assert response.status_code == 400
    obj = json.loads(response.data)
    assert "Missing required parameter" in obj['message']


def test_create(client):
    response = client.post('/api/organizations', data={
        "name": "edX",
        "default_allocation": "11.50",
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
    assert created["name"] == "edX"
