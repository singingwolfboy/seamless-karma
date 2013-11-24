from flask import render_template
from seamless_karma import app

@app.route('/')
def index():
    return render_template("base.html")
