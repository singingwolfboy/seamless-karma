from flask import Flask, render_template
from .models import db
from .extensions import sentry, heroku, cache, api
from .converters import ISODateConverter
from .context_processors import requirejs

def create_app(config=object()):
    app = Flask(__name__)
    app.config.from_object(config)

    register_url_converters(app)
    register_extensions(app)
    register_context_processors(app)

    @app.route('/')
    def index():
        return render_template("base.html")

    return app


def register_extensions(app):
    heroku.init_app(app)
    sentry.init_app(app)
    db.init_app(app)
    api.init_app(app)
    cache.init_app(app)


def register_url_converters(app):
    app.url_map.converters["date"] = ISODateConverter


def register_context_processors(app):
    app.context_processor(requirejs)
