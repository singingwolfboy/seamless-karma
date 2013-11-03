#!/usr/bin/env python

from flask.ext.script import Manager, prompt_bool
from sqlalchemy import create_engine
from seamless_karma import app, db
from seamless_karma.models import User, Organization, Order

manager = Manager(app)
dbmanager = Manager(usage="Perform database operations")


@dbmanager.command
def drop():
    "Drops database tables"
    if prompt_bool("Are you sure you want to lose all your data"):
        db.drop_all()
        db.session.commit()


@dbmanager.command
def create():
    "Creates database tables from sqlalchemy models"
    db.create_all()
    db.session.commit()


@dbmanager.command
def recreate():
    "Recreates database tables (same as issuing 'drop' and then 'create')"
    drop()
    create()


@dbmanager.command
def sql():
    "Dumps SQL for creating database tables"
    def dump(sql, *multiparams, **params):
        print(sql.compile(dialect=engine.dialect))
    engine = create_engine('postgresql://', strategy='mock', executor=dump)
    db.metadata.create_all(engine, checkfirst=False)


manager.add_command("db", dbmanager)


@manager.shell
def make_shell_context():
    return dict(app=app, db=db,
        User=User, Organization=Organization, Order=Order)

if __name__ == "__main__":
    manager.run()
