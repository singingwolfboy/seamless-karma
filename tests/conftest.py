try:
    import seamless_karma
except ImportError:
    import sys
    from path import path
    PROJ_DIR = path(__file__).parent.parent
    sys.path.insert(0, PROJ_DIR)
    import seamless_karma

import pytest
from seamless_karma import create_app, extensions


@pytest.fixture
def app(request):
    app = create_app("test")
    ctx = app.test_request_context()
    ctx.push()
    extensions.db.create_all()
    def fin():
        extensions.db.drop_all()
        ctx.pop()
    request.addfinalizer(fin)
    return app


@pytest.fixture
def db():
    return extensions.db


@pytest.fixture
def client(app):
    return app.test_client()

