# coding=utf-8
from __future__ import unicode_literals

import pytest
try:
    import seamless_karma
except ImportError:
    import sys
    from path import path
    PROJ_DIR = path(__file__).parent.parent
    sys.path.insert(0, PROJ_DIR)
    import seamless_karma
from seamless_karma import create_app, extensions


def pytest_addoption(parser):
    parser.addoption("--db", default="sqlite", metavar="BACKEND",
        help="database backend to use for running tests: sqlite or postgres")


@pytest.fixture
def app(request, pytestconfig):
    if pytestconfig.option.db == "postgres":
        app = create_app("test_postgres")
    else:
        app = create_app("test")
    ctx = app.test_request_context()
    ctx.push()
    extensions.db.create_all()
    def fin():
        extensions.db.session.remove()
        extensions.db.drop_all(app=app)
        extensions.db.get_engine(app).dispose()
        ctx.pop()
    request.addfinalizer(fin)
    return app


@pytest.fixture
def db():
    return extensions.db


@pytest.fixture
def client(app):
    return app.test_client()
