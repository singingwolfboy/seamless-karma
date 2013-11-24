#!/usr/bin/env python

from flask.ext.script import Manager, Server, prompt_bool
import sqlalchemy as sa
from seamless_karma import app, db
from seamless_karma.models import User, Organization, Order, OrderContribution
import subprocess as sp
import os.path
import hashlib

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
    engine = sa.create_engine('postgresql://', strategy='mock', executor=dump)
    db.metadata.create_all(engine, checkfirst=False)


manager.add_command("db", dbmanager)


@manager.shell
def make_shell_context():
    return dict(app=app, db=db, sa=sa,
        User=User, Organization=Organization, Order=Order,
        OrderContribution=OrderContribution)

def compile_config_js():
    if not os.path.isfile("seamless_karma/static/scripts/config.js"):
        sp.call(["./node_modules/coffee-script/bin/coffee", "--compile",
            "seamless_karma/static/scripts/config.coffee"])

class ServerWithPrerun(Server):
    def handle(self, *args, **kwargs):
        compile_config_js()
        super(ServerWithPrerun, self).handle(*args, **kwargs)

manager.add_command("runserver", ServerWithPrerun())

@manager.command
def build():
    "Build optimized JS for deployment"
    sp.call(["../../node_modules/bower/bin/bower", "install"],
        cwd="seamless_karma/static")
    compile_config_js()
    sp.call(["./node_modules/requirejs/bin/r.js", "-o", "build.js"])
    fname = "seamless_karma/static/scripts/optimized{hash}.js"
    with open(fname.format(hash="")) as f:
        content = f.read()
    hash = hashlib.md5(content).hexdigest()[0:8]
    with open(fname.format(hash="."+hash), "w") as f:
        f.write(content)



if __name__ == "__main__":
    manager.run()
