import factory
from factory import fuzzy
from factory.alchemy import SQLAlchemyModelFactory
from seamless_karma.extensions import db
from seamless_karma.models import (User, Organization, Vendor,
    Order, OrderContribution)
from decimal import Decimal
from datetime import date, time, datetime, timedelta
from string import ascii_uppercase


def make_username(user):
    return user.first_name[0] + user.last_name


class Factory(SQLAlchemyModelFactory):
    FACTORY_SESSION = db.session


class OrganizationFactory(Factory):
    FACTORY_FOR = Organization

    name = fuzzy.FuzzyText()
    default_allocation = fuzzy.FuzzyDecimal(low=0, high=25, precision=2)


class UserFactory(Factory):
    FACTORY_FOR = User

    first_name = fuzzy.FuzzyText()
    last_name = fuzzy.FuzzyText()
    username = factory.LazyAttribute(make_username)
    organization = factory.SubFactory(OrganizationFactory)


class VendorFactory(Factory):
    FACTORY_FOR = Vendor

    name = fuzzy.FuzzyText()


week_ago = date.today() - timedelta(days=7)
week_ahead = date.today() + timedelta(days=7)


class OrderFactory(Factory):
    FACTORY_FOR = Order

    for_date = fuzzy.FuzzyDate(week_ago, week_ahead)
    placed_at = fuzzy.FuzzyNaiveDateTime(datetime.combine(week_ago, time.min))
    vendor = factory.SubFactory(VendorFactory)
    ordered_by = factory.SubFactory(UserFactory)
    # contributors = factory.List([#factory.SubFactory(OrderContributionFactory))
    #     factory.RelatedFactory("factories.OrderContributionFactory", "order")
    # ])



class OrderContributionFactory(Factory):
    FACTORY_FOR = OrderContribution

    user = factory.SubFactory(UserFactory)
    order = factory.SubFactory(OrderFactory)
    amount = fuzzy.FuzzyDecimal(low=0, high=15, precision=2)

