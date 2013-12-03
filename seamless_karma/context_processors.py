from flask import url_for, config, Markup, current_app
from seamless_karma.extensions import cache
import hashlib

@cache.cached(timeout=60, key_prefix="optimized_js")
def optimized_js_hash():
    fname = "seamless_karma/static/scripts/optimized.js"
    with open(fname.format(hash="")) as f:
        content = f.read()
    return hashlib.md5(content).hexdigest()[0:8]


def requirejs():
    if current_app.debug:
        main = url_for('static', filename="scripts/config")
        src = url_for('static', filename="bower_components/requirejs/require.js")
        script = '<script data-main="{main}" src="{src}"></script>'.format(
            main=main, src=src)
    else:
        hash = optimized_js_hash()
        fname = "scripts/optimized.{hash}.js".format(hash=hash)
        src = url_for('static', filename=fname)
        script = '<script src="{src}"></script>'.format(src=src)
    return {"requirejs": Markup(script)}
