from seamless_karma import app

@app.route('/')
def index():
    return "seamless karma"
