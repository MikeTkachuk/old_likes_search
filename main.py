import os
import flask
import time
import numpy as np
import tweepy as tw
from tweepy.auth import OAuthHandler
from tweepy.api import API

# auth = OAuthHandler()

app = flask.Flask('likes_search')


@app.route('/')
def render_index():
    flask.render_template('index.html')


app.run()
