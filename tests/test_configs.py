# coding=utf-8
from __future__ import unicode_literals

from seamless_karma import create_app


def test_create_app_test_mode():
    app = create_app("test")
    assert app.config["TESTING"] is True
    assert "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]


def test_create_app_test_postgres_mode():
    app = create_app("test_postgres")
    assert app.config["TESTING"] is True
    assert "postgres" in app.config["SQLALCHEMY_DATABASE_URI"]


def test_create_app_dev_mode():
    app = create_app("dev")
    assert app.debug is True


def test_create_app_prod_mode():
    app = create_app("prod")
    assert app.debug is False
