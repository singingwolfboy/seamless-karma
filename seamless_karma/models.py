from seamless_karma import db
from sqlalchemy import select, func
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from decimal import Decimal


class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True, nullable=False)
    default_allocation = db.Column(db.Numeric(scale=2))

    def __repr__(self):
        return u"<Organization {!r}>".format(self.name)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(256), unique=True, nullable=False)
    first_name = db.Column(db.String(256), nullable=False)
    last_name = db.Column(db.String(256), nullable=False)
    allocation = db.Column(db.Numeric(scale=2), nullable=False)

    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'),
        nullable=False)
    organization = db.relationship(Organization,
        backref=db.backref('users', lazy="dynamic"))

    def __init__(self, username, first_name, last_name, organization, allocation=None):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.organization = organization
        self.allocation = allocation or organization.default_allocation

    def __repr__(self):
        return u'<User "{first} {last}">'.format(
            first=self.first_name, last=self.last_name)

    @hybrid_property
    def contributed_orders(self):
        """
        All orders that this user contributed to, but did not place.
        """
        return (o for o in self.orders if o.ordered_by_id != self.id)

    @contributed_orders.expression
    def contributed_orders(cls):
        return (Order.join(OrderContribution)
            .filter(OrderContribution.user_id == cls.id)
            .filter(Order.user_id != cls.id)
        )

    @hybrid_property
    def karma(self):
        """
        Total amount this user has contributed to other peoples' orders,
        minus total amount others have contributed to this user's orders.
        """
        total = (sum(oc.amount for oc in self.order_contributions if oc.is_external)
               - sum(o.external_contribution for o in self.own_orders))
        return total or Decimal('0.00')

    @karma.expression
    def karma(cls):
        positive = (
            db.session.query(func.sum(OrderContribution.amount).label('pos'))
                .join(Order)
                .filter(OrderContribution.user_id == cls.id)
                .filter(Order.ordered_by_id != cls.id)
        )
        negative = (
            db.session.query(func.sum(OrderContribution.amount).label('neg'))
                .join(Order)
                .filter(OrderContribution.user_id != cls.id)
                .filter(Order.ordered_by_id == cls.id)
        )
        return db.session.query(func.coalesce(
            positive.subquery().columns.pos - negative.subquery().columns.neg,
            Decimal('0.00')
        ).label('karma'))

    @hybrid_method
    def unallocated(self, date):
        allocated = sum(o.user_contribution(self.id) for o in self.orders
            if o.for_date == date) or Decimal('0.00')
        return self.allocation - allocated

    @unallocated.expression
    def unallocated(cls, date):
        # return (db.session.query(
        #         (cls.allocation - func.coalesce(
        #             func.sum(OrderContribution.amount),
        #             Decimal('0.00')
        #         )).label('unallocated')
        #     )
        #     .join(Order).join(OrderContribution)
        #     .filter(Order.for_date == date)
        # )
        allocated = (db.session.query(
            func.coalesce(
                func.sum(OrderContribution.amount),
                Decimal('0.00')
            ).label('allocated'))
            .join(Order)
            .filter(Order.for_date == date)
        )
        return db.session.query(
            cls.allocation - allocated.subquery().columns.allocated)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    for_date = db.Column(db.Date, nullable=False)
    placed_at = db.Column(db.DateTime, nullable=False)
    restaurant = db.Column(db.String(256))

    ordered_by_id = db.Column(db.Integer, db.ForeignKey('user.id'),
        nullable=False)
    ordered_by = db.relationship(User,
        backref="own_orders")
    contributors = db.relationship(User,
        secondary="order_contribution",
        backref="orders")

    def __repr__(self):
        return u"<Order {date}>".format(date=self.for_date.isoformat())

    @classmethod
    def create(cls, for_date, placed_at, restaurant, ordered_by_id, contributions):
        order = cls(
            for_date=for_date,
            placed_at=placed_at,
            restaurant=restaurant,
            ordered_by_id=ordered_by_id,
        )
        for contributor_id, amount in contributions.items():
            oc = OrderContribution(
                user_id=contributor_id,
                amount=amount,
                order=order,
            )
        return order

    @hybrid_property
    def total_amount(self):
        return sum(oc.amount for oc in self.contributions)

    @total_amount.expression
    def total_amount(cls):
        return (select([func.sum(OrderContribution.amount)])
            .where(OrderContribution.order_id == cls.id)
            .label('total_amount'))

    @hybrid_property
    def personal_contribution(self):
        return sum(oc.amount for oc in self.contributions
            if oc.user_id == self.ordered_by_id)

    @personal_contribution.expression
    def personal_contribution(cls):
        return (select([func.sum(OrderContribution.amount)])
            .where(OrderContribution.order_id == cls.id)
            .where(OrderContribution.user_id == cls.ordered_by_id)
            .label('personal_contribution'))

    @hybrid_property
    def external_contribution(self):
        return sum(oc.amount for oc in self.contributions
            if oc.user_id != self.ordered_by_id)

    @external_contribution.expression
    def external_contribution(cls):
        return (select([func.sum(OrderContribution.amount)])
            .where(OrderContribution.order_id == cls.id)
            .where(OrderContribution.user_id != cls.ordered_by_id)
            .label('external_contribution'))

    @hybrid_method
    def user_contribution(self, user_id):
        total = sum(oc.amount for oc in self.contributions
            if oc.user_id == user_id)
        return total or Decimal('0.00')

    @user_contribution.expression
    def user_contribution(cls, user_id):
        return (db.session.query(
            func.coalesce(
                func.sum(OrderContribution.amount),
                Decimal('0.00')
            ))
            .join(cls)
            .filter(OrderContribution.user_id == user_id)
        )


class OrderContribution(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
        primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'),
        primary_key=True)

    user = db.relationship(User, backref="order_contributions")
    order = db.relationship(Order, backref="contributions",
        cascade="all, delete, delete-orphan", single_parent=True)
    amount = db.Column(db.Numeric(scale=2), nullable=False)

    def __repr__(self):
        return u"<OrderContribution {}>".format(self.amount)

    @hybrid_property
    def beneficiary(self):
        return self.order.ordered_by

    @hybrid_property
    def is_external(self):
        return self.user_id != self.order.ordered_by_id
