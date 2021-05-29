import os
import flask
import sys
import oauth2 as oauth
import tweepy as tw
from tweepy.auth import OAuthHandler
from tweepy.api import API


app = flask.Flask('likes_search')


@app.route('/')
def render_index():
    return flask.render_template('index.html')


app.run()
