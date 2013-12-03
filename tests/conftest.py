try:
    import seamless_karma
except ImportError:
    import sys
    from path import path
    PROJ_DIR = path(__file__).parent.parent
    sys.path.insert(0, PROJ_DIR)
    import seamless_karma

import pytest
from seamless_karma import create_app

@pytest.fixture
def app():
    return create_app("test")

@pytest.fixture
def client(app):
    return app.test_client()