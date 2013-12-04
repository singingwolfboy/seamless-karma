import json
import pytest
from seamless_karma.models import db, User
import factory

def test_empty(client):
    response = client.get('/api/users')
    assert response.status_code == 200
    obj = json.loads(response.data)
    assert obj['count'] == 0


@pytest.fixture
def users(app, OrganizationFactory, UserFactory):
    org = OrganizationFactory.create()
    u1 = UserFactory.create(organization=org)
    u2 = UserFactory.create(organization=org)
    db.session.commit()
    return [u1, u2]


def test_contents(client, users):
    response = client.get('/api/users')
    assert response.status_code == 200
    obj = json.loads(response.data)
    assert obj['count'] == len(users)
    assert obj['data'][0]['first_name'] == users[0].first_name
    assert obj['data'][1]['username'] == users[1].username


