import json
import pytest
from seamless_karma.extensions import db
from factories import OrganizationFactory, UserFactory
from six.moves.urllib.parse import urlparse


def test_empty(client):
    response = client.get('/api/users')
    assert response.status_code == 200
    obj = json.loads(response.get_data(as_text=True))
    assert obj['count'] == 0


@pytest.fixture
def users(app):
    org = OrganizationFactory.create()
    u1 = UserFactory.create(organization=org)
    u2 = UserFactory.create(organization=org)
    db.session.commit()
    return [u1, u2]


def test_existing(client, users):
    response = client.get('/api/users')
    assert response.status_code == 200
    obj = json.loads(response.get_data(as_text=True))
    assert obj['count'] == len(users)
    assert obj['data'][0]['first_name'] == users[0].first_name
    assert obj['data'][1]['username'] == users[1].username


def test_create_no_args(client):
    response = client.post('/api/users')
    assert response.status_code == 400
    obj = json.loads(response.get_data(as_text=True))
    assert "Missing required parameter" in obj['message']


def test_create(client):
    org = OrganizationFactory.create()
    db.session.commit()
    response = client.post('/api/users', data={
        "username": "AAgarwal",
        "first_name": "Anant",
        "last_name": "Agarwal",
        "organization_id": org.id,
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
    assert created["username"] == "AAgarwal"


def test_create_duplicate(client):
    org = OrganizationFactory.create()
    UserFactory.create(username="AAgarwal", organization=org)
    db.session.commit()
    response = client.post('/api/users', data={
        "username": "AAgarwal",
        "first_name": "Anant",
        "last_name": "Agarwal",
        "organization_id": org.id,
    })
    assert response.status_code == 400
    obj = json.loads(response.get_data(as_text=True))
    assert "User with username AAgarwal already exists" == obj["message"]


def test_users_by_org(client):
    o1 = OrganizationFactory.create()
    u1 = UserFactory.create(organization=o1)
    o2 = OrganizationFactory.create()
    u2 = UserFactory.create(organization=o2)
    u3 = UserFactory.create(organization=o2)
    db.session.commit()

    o1_url = "/api/organizations/{0.id}/users".format(o1)
    o1_resp = client.get(o1_url)
    assert o1_resp.status_code == 200
    o1_obj = json.loads(o1_resp.get_data(as_text=True))
    assert o1_obj["count"] == 1
    assert o1_obj["data"][0]["first_name"] == u1.first_name

    o2_url = "/api/organizations/{0.id}/users".format(o2)
    o2_resp = client.get(o2_url)
    assert o2_resp.status_code == 200
    o2_obj = json.loads(o2_resp.get_data(as_text=True))
    assert o2_obj["count"] == 2
    assert o2_obj["data"][0]["first_name"] == u2.first_name
    assert o2_obj["data"][1]["last_name"] == u3.last_name


def test_users_by_org_name(client):
    o1 = OrganizationFactory.create()
    u1 = UserFactory.create(organization=o1)
    o2 = OrganizationFactory.create()
    u2 = UserFactory.create(organization=o2)
    u3 = UserFactory.create(organization=o2)
    db.session.commit()

    o1_url = "/api/organizations/{0.name}/users".format(o1)
    o1_resp = client.get(o1_url)
    assert o1_resp.status_code == 200
    o1_obj = json.loads(o1_resp.get_data(as_text=True))
    assert o1_obj["count"] == 1
    assert o1_obj["data"][0]["first_name"] == u1.first_name

    o2_url = "/api/organizations/{0.name}/users".format(o2)
    o2_resp = client.get(o2_url)
    assert o2_resp.status_code == 200
    o2_obj = json.loads(o2_resp.get_data(as_text=True))
    assert o2_obj["count"] == 2
    assert o2_obj["data"][0]["first_name"] == u2.first_name
    assert o2_obj["data"][1]["last_name"] == u3.last_name
