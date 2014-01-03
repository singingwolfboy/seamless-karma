import json
import pytest
from seamless_karma.extensions import db
from seamless_karma.models import User
from factories import OrganizationFactory, UserFactory
from six.moves.urllib.parse import urlparse

def test_empty(client):
    response = client.get('/api/users')
    assert response.status_code == 200
    obj = json.loads(response.data)
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
    obj = json.loads(response.data)
    assert obj['count'] == len(users)
    assert obj['data'][0]['first_name'] == users[0].first_name
    assert obj['data'][1]['username'] == users[1].username


def test_create_no_args(client):
    response = client.post('/api/users')
    assert response.status_code == 400
    obj = json.loads(response.data)
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
    obj = json.loads(response.data)
    assert "id" in obj
    url = response.headers["Location"]
    path = urlparse(url).path
    resp2 = client.get(path)
    assert resp2.status_code == 200
    created = json.loads(resp2.data)
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
    obj = json.loads(response.data)
    assert "IntegrityError" in obj["message"]
