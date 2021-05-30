import sys
import os
import flask
from flask import Flask, render_template, request, url_for
import oauth2 as oauth
import urllib

import tweepy as tw
from tweepy.auth import OAuthHandler
from tweepy.api import API

def to_log(*msg):
    for i in msg:
        print('************ ' + i)


app = flask.Flask(__name__)

request_token_url = 'https://api.twitter.com/oauth/request_token'
access_token_url = 'https://api.twitter.com/oauth/access_token'
authorize_url = 'https://api.twitter.com/oauth/authorize'
show_user_url = 'https://api.twitter.com/1.1/users/show.json'


app.config['APP_CONSUMER_KEY'] = os.getenv(
    'CONSUMER_KEY', '-1')
app.config['APP_CONSUMER_SECRET'] = os.getenv(
    'CONSUMER_SECRET', '-1')
to_log('got env vars',app.config['APP_CONSUMER_KEY'][0]+app.config['APP_CONSUMER_SECRET'][0])

oauth_store = {}

@app.route('/')
def render_index():
    app_callback_url = url_for('callback',_external=True)

    consumer = oauth.Consumer(app.config["APP_CONSUMER_KEY"],app.config["APP_CONSUMER_SECRET"])
    client = oauth.Client(consumer)

    resp, content = client.request(request_token_url, "POST", body=urllib.parse.urlencode({
        "oauth_callback": app_callback_url}))

    if int(resp['status']) != 200:
        to_log("authorization unsuccessful",f": resp status {resp['status']}, msg: {content.decode('utf-8')}")
        sys.stdout.flush()
        return flask.render_template('index.html')
    else:
        to_log("SUCCESS",f": resp status {resp['status']}, msg: {content.decode('utf-8')}")
        request_token = dict(urllib.parse.parse_qsl(content))
        oauth_token = request_token[b'oauth_token'].decode('utf-8')
        oauth_token_secret = request_token[b'oauth_token_secret'].decode('utf-8')
        oauth_store["oauth_secret"] = oauth_token_secret

    return flask.render_template('index.html',
                                 authorize_url=authorize_url,
                                 oauth_token=oauth_token)

@app.route('/callback')
def callback():
    return render_template('index.html')


if __name__ == '__main__':
    app.run()

