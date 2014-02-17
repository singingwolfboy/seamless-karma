#!/usr/bin/env python
from seamless_karma import create_app
from seamless_karma.models import db, User, Organization, Order, OrderContribution
from flask import current_app
from flask.ext.script import Manager, prompt_bool
import sqlalchemy as sa
import subprocess as sp
import os
from path import path
import hashlib


manager = Manager(create_app)
manager.add_option('-c', '--config', required=False, default='prod')


@manager.shell
def make_shell_context():
    return dict(
        db=db, sa=sa, app=current_app,
        User=User, Organization=Organization, Order=Order,
        OrderContribution=OrderContribution
    )


@manager.option('--dry-run', action='store_true', default=False)
@manager.option('--noinput', dest='input', action='store_false', default=True)
def collectstatic(dry_run, input):
    """
    Collect static assets for deployment.

    This intentionally has the same call signature as Django's collectstatic
    command, so that Heroku's Python buildpack will call it automatically.
    """
    # if we were deployed without node.js support, raise error
    try:
        sp.check_call(["which", "node"], stdout=sp.PIPE)
    except sp.CalledProcessError:
        raise RuntimeError("cannot collectstatic; node is not installed")

    if dry_run:
        # do nothing -- this is just the Python buildpack checking if we
        # support collectstatic
        return

    static_dir = path.getcwd() / "seamless_karma" / "static"
    sp.call(["../../node_modules/bower/bin/bower", "install"], cwd=static_dir)
    sp.call(["./node_modules/requirejs/bin/r.js", "-o", "amd.build.js"])
    # copy optimized.js based on hash of contents
    optimized_js = static_dir / "scripts" / "optimized.js"
    text = optimized_js.text()
    hash = hashlib.md5(text).hexdigest()[0:8]
    optimized_hash = optimized_js.parent / "optimized.{}.js".format(hash)
    # if we have a sourcemap comment, rewrite it
    text = text.replace(
        "//# sourceMappingURL=optimized.js.map",
        "//# sourceMappingURL=optimized.{}.js.map".format(hash)
    )
    print("Copying {src} to {dest}".format(
        src=optimized_js.name, dest=optimized_hash.name))
    optimized_hash.write_text(text)
    # if we have a sourcemap, copy it too
    sourcemap = optimized_js + ".map"
    if sourcemap.exists():
        sourcemap_hash = optimized_hash + ".map"
        print("Copying {src} to {dest}".format(
            src=sourcemap.name, dest=sourcemap_hash.name))
        sourcemap.copy(sourcemap_hash)
    # update optimized.latest.js symlink
    latest_js = optimized_hash.parent / "optimized.latest.js"
    if latest_js.exists():
        latest_js.remove()
    print("Updating {name} symlink".format(name=latest_js.name))
    os.symlink(optimized_hash.name, latest_js)
    # and latest sourcemap symlink
    latest_sourcemap = latest_js + ".map"
    if latest_sourcemap.exists():
        latest_sourcemap.remove()
    if sourcemap.exists():
        print("Updating {name} symlink".format(name=latest_sourcemap.name))
        os.symlink(sourcemap_hash.name, latest_sourcemap)


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
# the "node" binary lives in /app/vendor/node/bin, so make sure that's on the PATH
def add_local_bin_to_path():
    local_bin = path.getcwd() / "vendor" / "node" / "bin"
    paths = os.environ['PATH'].split(":")
    if not local_bin in paths:
        paths.insert(0, local_bin)
        os.environ['PATH'] = ":".join(paths)


if __name__ == "__main__":
    add_local_bin_to_path()
    manager.run()
