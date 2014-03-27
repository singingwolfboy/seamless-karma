# coding=utf-8
from __future__ import unicode_literals

from factories import OrganizationFactory, UserFactory, VendorFactory
from seamless_karma.models import Order, OrderContribution
from seamless_karma.extensions import db
from decimal import Decimal
from datetime import datetime, date


def test_order_allocations(app):
    org = OrganizationFactory.create()
    u1 = UserFactory.create(organization=org)
    u2 = UserFactory.create(organization=org)
    u3 = UserFactory.create(organization=org)
    vendor = VendorFactory.create()
    order = Order(
        ordered_by=u1, vendor=vendor,
        for_date=date.today(), placed_at=datetime.now(),
    )
    db.session.add(order)
    db.session.commit()
    assert order.total_amount == Decimal("0.00")
    oc1 = OrderContribution(order=order, user=u1, amount=Decimal("10.80"))
    db.session.add(oc1)
    db.session.commit()
    assert order.total_amount == Decimal("10.80")
    oc2 = OrderContribution(order=order, user=u2, amount=Decimal("2.50"))
    db.session.add(oc2)
    db.session.commit()
    assert order.total_amount == Decimal("13.30")
    oc3 = OrderContribution(order=order, user=u3, amount=Decimal("4.75"))
    db.session.add(oc3)
    db.session.commit()
    assert order.total_amount == Decimal("18.05")
