import flask


app = flask.Flask('likes_search')


@app.route('/')
def render_index():
    return flask.render_template('index.html')


app.run()
