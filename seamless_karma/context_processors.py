from flask import url_for, config, Markup, current_app
from seamless_karma.extensions import cache
from dealer.git import git

def requirejs():
    if current_app.debug:
        main = url_for('static', filename="scripts/config")
        src = url_for('static', filename="bower_components/requirejs/require.js")
        script = '<script data-main="{main}" src="{src}"></script>'.format(
            main=main, src=src)
    else:
        hash = cache.get("{rev}|optimized_js_hash".format(git.revision)) or ""
        fname = "scripts/optimized{hash}.js".format(hash=hash)
        src = url_for('static', filename=fname)
        script = '<script src="{src}"></script>'.format(src=src)
    return {"requirejs": Markup(script)}
