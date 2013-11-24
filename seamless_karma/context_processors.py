from seamless_karma import app
from flask import url_for, config, Markup

@app.context_processor
def requirejs():
    if app.debug:
        main = url_for('static', filename="scripts/config")
        src = url_for('static', filename="bower_components/requirejs/require.js")
        script = '<script data-main="{main}" src="{src}"></script>'.format(
            main=main, src=src)
    else:
        # TODO: get latest optimized hash
        fname = "scripts/optimized.js"
        src = url_for('static', filename=fname)
        script = '<script src="{src}"></script>'.format(src=src)
    return {"requirejs": Markup(script)}
