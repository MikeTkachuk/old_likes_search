import sys
import os
import flask
from flask import Flask, render_template, request, url_for
import oauth2 as oauth
import urllib

import tweepy as tw
from tweepy.auth import OAuthHandler
from tweepy.api import API

sys.stdout.write('test string')
sys.stdout.flush()
try:
    app = flask.Flask('likes_search')

    request_token_url = 'https://api.twitter.com/oauth/request_token'
    access_token_url = 'https://api.twitter.com/oauth/access_token'
    authorize_url = 'https://api.twitter.com/oauth/authorize'
    show_user_url = 'https://api.twitter.com/1.1/users/show.json'

    try:
        app.config['APP_CONSUMER_KEY'] = os.getenv(
            'CONSUMER_KEY', '-1')
        app.config['APP_CONSUMER_SECRET'] = os.getenv(
            'CONSUMER_SECRET', '-1')
    except e:
        app.config['APP_CONSUMER_KEY'] = "JfbzKUTtNl3JXISoRpU"+str(2)+"eB67F" + '1'
        app.config['APP_CONSUMER_SECRET'] = "OdvZEgIIg3qu7GNzPLvn31U0"+str(9)+"rin6FNyFBMvkl9Gxkm1nAlAPz" + '9'


    @app.route('/')
    def render_index():
        app_callback_url = url_for('render_index',_external=True)

        consumer = oauth.Consumer(app.config["APP_CONSUMER_KEY"],app.config["APP_CONSUMER_SECRET"])
        client = oauth.Client(consumer)

        resp, content = client.request(request_token_url, "POST", body=urllib.parse.urlencode({
            "oauth_callback": app_callback_url}))

        if resp['status'] != 200:
            print("authorization unsuccessful")
            return flask.render_template('index.html')
        else:
            request_token = dict(urllib.parse.parse_qsl(content))
            oauth_token = request_token[b'oauth_token'].decode('utf-8')
            oauth_token_secret = request_token[b'oauth_token_secret'].decode('utf-8')

        return flask.render_template('index.html',
                                     authorize_url=authorize_url,
                                     oauth_token=oauth_token,
                                     oauth_token_secret=oauth_token_secret)


    app.run(debug=True)
except e:
    sys.stdout.write(str(e))
