import factory
from factory.alchemy import SQLAlchemyModelFactory
from seamless_karma.extensions import db
from seamless_karma.models import (User, Organization, Vendor,
    Order, OrderContribution)
from decimal import Decimal
from datetime import date, datetime
from string import ascii_uppercase


def make_first_name(n):
    return "{initial}name".format(
        initial=ascii_uppercase[n-1])

def make_username(user):
    return user.first_name[0] + user.last_name


class Factory(SQLAlchemyModelFactory):
    FACTORY_SESSION = db.session


class OrganizationFactory(Factory):
    FACTORY_FOR = Organization

    name = 'edX'
    default_allocation = Decimal('11.50')


class UserFactory(Factory):
    FACTORY_FOR = User

    first_name = factory.Sequence(make_first_name)
    last_name = 'Example'
    username = factory.LazyAttribute(make_username)
    organization = factory.SubFactory(OrganizationFactory)


class VendorFactory(Factory):
    FACTORY_FOR = Vendor

    name = factory.Sequence(make_first_name)


class OrderFactory(Factory):
    FACTORY_FOR = Order

    for_date = date.today()
    placed_at = datetime.utcnow()
    vendor = factory.SubFactory(VendorFactory)
    ordered_by = factory.SubFactory(UserFactory)
    #contributors = factory.List(factory.SubFactory(OrderContributionFactory))


class OrderContributionFactory(Factory):
    FACTORY_FOR = OrderContribution

    user = factory.SubFactory(UserFactory)
    order = factory.SubFactory(OrderFactory)
    amount = Decimal('8.52')

