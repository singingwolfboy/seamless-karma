#!/usr/bin/env python
from seamless_karma import create_app
from seamless_karma.models import db, User, Organization, Order, OrderContribution
from seamless_karma.extensions import cache
from flask.ext.script import Manager, Server, prompt_bool
import sqlalchemy as sa
import subprocess as sp
import os
from path import path
import hashlib
from dealer.git import git


manager = Manager(create_app)
manager.add_option('-c', '--config', required=False, default='prod')


@manager.shell
def make_shell_context():
    return dict(db=db, sa=sa,
        User=User, Organization=Organization, Order=Order,
        OrderContribution=OrderContribution)

def compile_config_js():
    if not path("seamless_karma/static/scripts/config.js").isfile():
        sp.call(["./node_modules/coffee-script/bin/coffee", "--compile",
            "seamless_karma/static/scripts/config.coffee"])

class ServerWithPrerun(Server):
    def handle(self, *args, **kwargs):
        self.prerun()
        super(ServerWithPrerun, self).handle(*args, **kwargs)

    def prerun(self):
        compile_config_js()

manager.add_command("runserver", ServerWithPrerun())


@manager.option('--dry-run', action='store_true', default=False)
@manager.option('--noinput', dest='input', action='store_false', default=True)
def collectstatic(dry_run, input):
    """
    Collect static assets for deployment.

    This intentionally has the same call signature as Django's collectstatic
    command, so that Heroku's Python buildpack will call it automatically.
    """
    if dry_run:
        # do nothing -- this is just the Python buildpack checking if we
        # support collectstatic
        return

    static_dir = path.getcwd() / "seamless_karma" / "static"
    sp.call(["../../node_modules/bower/bin/bower", "install"], cwd=static_dir)
    compile_config_js()
    sp.call(["./node_modules/requirejs/bin/r.js", "-o", "build.js"])
    fname = "seamless_karma/static/scripts/optimized{hash}.js"
    with open(fname.format(hash="")) as f:
        content = f.read()
    hash = "." + hashlib.md5(content).hexdigest()[0:8]
    with open(fname.format(hash=hash), "w") as f:
        f.write(content)
    cache.set("{rev}|optimized_js_hash".format(git.revision), hash)


### DATABASE MANAGEMENT ###
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


### HEROKU SETUP ###
# the "node" binary lives in /app/bin, so make sure that's on the PATH
def add_local_bin_to_path():
    local_bin = path.getcwd() / "bin"
    paths = os.environ['PATH'].split(":")
    if not local_bin in paths:
        paths.insert(0, local_bin)
        os.environ['PATH'] = ":".join(paths)


if __name__ == "__main__":
    add_local_bin_to_path()
    manager.run()
