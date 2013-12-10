import pytest
from seamless_karma import create_app

def test_create_app_test_mode():
    app = create_app("test")
    assert app.config["TESTING"] == True
    assert "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]

def test_create_app_dev_mode():
    app = create_app("dev")
    assert app.debug == True

def test_create_app_prod_mode():
    app = create_app("prod")
    assert app.debug == False
