# coding=utf-8
from __future__ import unicode_literals

from flask import url_for, Markup, current_app
from path import path


def requirejs():
    scripts_dir = path(__file__).parent / "static" / "scripts"
    latest_js = scripts_dir / "optimized.latest.js"
    if not current_app.debug and latest_js.exists():
        fname = "scripts/{}".format(latest_js.readlink())
        src = url_for('static', filename=fname)
        script = '<script src="{src}"></script>'.format(src=src)
    else:
        main = url_for('static', filename="scripts/config")
        src = url_for('static', filename="bower_components/requirejs/require.js")
        script = '<script data-main="{main}" src="{src}"></script>'.format(
            main=main, src=src)
    return {"requirejs": Markup(script)}
