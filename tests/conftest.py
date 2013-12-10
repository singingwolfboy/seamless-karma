try:
    import seamless_karma
except ImportError:
    import sys
    from path import path
    PROJ_DIR = path(__file__).parent.parent
    sys.path.insert(0, PROJ_DIR)
    import seamless_karma

import pytest
from seamless_karma import create_app, models
import factory
from factory.alchemy import SQLAlchemyModelFactory
from decimal import Decimal
from string import ascii_uppercase


@pytest.fixture
def app(request):
    app = create_app("test")
    ctx = app.test_request_context()
    ctx.push()
    models.db.create_all()
    def fin():
        models.db.drop_all()
        ctx.pop()
    request.addfinalizer(fin)
    return app


@pytest.fixture
def db():
    return models.db


@pytest.fixture
def client(app):
    return app.test_client()


def make_first_name(n):
    return "{initial}name".format(
        initial=ascii_uppercase[n-1])

def make_username(user):
    return user.first_name[0] + user.last_name


class Factory(SQLAlchemyModelFactory):
    FACTORY_SESSION = models.db.session


@pytest.fixture
def OrganizationFactory():
    class OrganizationFactory(Factory):
        FACTORY_FOR = models.Organization

        name = 'edX'
        default_allocation = Decimal('11.50')

    return OrganizationFactory


@pytest.fixture
def UserFactory(OrganizationFactory):
    class UserFactory(Factory):
        FACTORY_FOR = models.User

        first_name = factory.Sequence(make_first_name)
        last_name = 'Example'
        username = factory.LazyAttribute(make_username)
        organization = factory.SubFactory(OrganizationFactory)

    return UserFactory


@pytest.fixture
def VendorFactory():
    class VendorFactory(Factory):
        FACTORY_FOR = models.Vendor

        name = factory.Sequence(make_first_name)

    return VendorFactory
