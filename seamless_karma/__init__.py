from flask import Flask, render_template
from .extensions import sentry, heroku, db, cache, api
from .converters import ISODateConverter
from .context_processors import requirejs
from path import path


def create_app(config=None):
    app = Flask(__name__)
    if config is not None:
        config_dir = path(__file__).parent / "config"
        configs = {}
        for f in config_dir.files():
            configs[f.namebase] = config_dir / f
        # support aliasing: "dev" => "config/dev.py"
        config = configs.get(config, config)
        app.config.from_pyfile(config)

    register_url_converters(app)
    register_extensions(app)
    register_context_processors(app)

    @app.route('/')
    def index():
        return render_template("base.html")

    return app


def register_extensions(app):
    heroku.init_app(app)
    # only setup sentry if we're not in debug mode: we don't want
    # sentry to log exceptions that developers are already seeing
    if not app.debug:
        sentry.init_app(app)

    db.init_app(app)
    api.init_app(app)
    cache.init_app(app)


def register_url_converters(app):
    app.url_map.converters["date"] = ISODateConverter


def register_context_processors(app):
    app.context_processor(requirejs)
