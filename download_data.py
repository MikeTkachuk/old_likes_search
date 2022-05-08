"""
A script to download the users likes data locally
"""

import sys
import os
import flask
from flask import Flask, render_template, request, url_for, session, jsonify
from flask_session import Session
from flask_cors import CORS, cross_origin
import oauth2 as oauth
import urllib
import datetime
import requests
import json
from tqdm import tqdm
from multiprocessing import Pool, Process

import tweepy as tw
from tweepy.auth import OAuthHandler
from tweepy.api import API

request_token_url = 'https://api.twitter.com/oauth/request_token'
access_token_url = 'https://api.twitter.com/oauth/access_token'
authorize_url = 'https://api.twitter.com/oauth/authorize'
show_user_url = 'https://api.twitter.com/1.1/users/show.json'

APP_CONSUMER_KEY = -1
APP_CONSUMER_SECRET = -1

def to_log(*msg):
    for i in msg:
        print('************ ' + str(i))
    sys.stdout.flush()


def write_cache(key, item, dir_='oauth_store'):
    if session.get(dir_, None) is None:
        session[dir_] = {}
    session[dir_][key] = item


def date_to_id(date: str):
    return int(
        (datetime.datetime.strptime(date, "%Y-%m-%d").timestamp() - 1288834975) * 2 ** 22 * 1000
    )


app = flask.Flask(__name__)

app.secret_key = "gs67hduyhw9nn7u"
app.config.from_object(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

Session(app)


@app.route('/')
@cross_origin()
def render_index():
    session["form_values"] = {"user": '',
                              "from": '',
                              "to": ''
                              }
    session["extension_cursor"] = ''

    if session.get('user', None) is None:
        return flask.redirect(url_for('signin'))
    else:
        return flask.render_template('download_data.html', ids=json.dumps([]), **session["form_values"])


@app.route('/signin')
def signin():
    app_callback_url = url_for('callback', _external=True)
    """dgfs"""
    to_log(app_callback_url)
    """sfgd"""
    consumer = oauth.Consumer(app.config["APP_CONSUMER_KEY"], app.config["APP_CONSUMER_SECRET"])
    client = oauth.Client(consumer)

    resp, content = client.request(request_token_url, "POST", body=urllib.parse.urlencode({
        "oauth_callback": app_callback_url}))

    if int(resp['status']) != 200:
        to_log("authorization unsuccessful", f": resp status {resp['status']}, msg: {content.decode('utf-8')}")
        return flask.render_template('index.html')
    else:
        to_log("SUCCESS", f": resp status {resp['status']}, msg: {content.decode('utf-8')}")
        request_token = dict(urllib.parse.parse_qsl(content))
        oauth_token = request_token[b'oauth_token'].decode('utf-8')
        oauth_token_secret = request_token[b'oauth_token_secret'].decode('utf-8')
        write_cache(oauth_token, oauth_token_secret)

    return flask.render_template('index.html',
                                 authorize_url=authorize_url,
                                 oauth_token=oauth_token)


@app.route('/signout')
def signout():
    session['user'] = None
    return flask.redirect(url_for('render_index'))


@app.route('/callback')
def callback():
    print('c')
    oauth_token = request.args.get('oauth_token')
    oauth_verifier = request.args.get('oauth_verifier')

    if oauth_token in session.get('oauth_store', {}):
        oauth_token_secret = session['oauth_store'][oauth_token]
    else:
        oauth_token_secret = -1
        to_log('secret local copy not found')
        return flask.redirect(url_for('render_index'))
    consumer = oauth.Consumer(
        app.config['APP_CONSUMER_KEY'], app.config['APP_CONSUMER_SECRET'])
    token = oauth.Token(oauth_token, oauth_token_secret)
    token.set_verifier(oauth_verifier)
    client = oauth.Client(consumer, token)

    resp, content = client.request(access_token_url, "POST")
    access_token = dict(urllib.parse.parse_qsl(content))

    real_oauth_token = access_token[b'oauth_token'].decode('utf-8')
    real_oauth_token_secret = access_token[b'oauth_token_secret'].decode(
        'utf-8')
    session['user'] = (real_oauth_token, real_oauth_token_secret)
    return flask.redirect(url_for('render_index'))


def download_likes(*args):
    auth = OAuthHandler(args[0], args[1])
    auth.set_access_token(*args[2])
    api = API(auth, wait_on_rate_limit=True)

    user_name = args[3]
    num = args[4]
    to = None

    favorites_params = {"screen_name": user_name,
                        "count": 200,
                        'include_entities': True,
                        }
    for i_get in tqdm(range(int(num) // favorites_params['count'] + 1)):
        if to is not None:
            favorites_params["max_id"] = to

        results = api.favorites(**favorites_params, tweet_mode='extended')
        for status in results:
            with open(f'downloads/{status.id}.json', 'w') as f:
                json.dump(status._json, f)
        to = results[-1].id


@app.route('/query')
def query():
    download_likes(app.config['APP_CONSUMER_KEY'],
                   app.config['APP_CONSUMER_SECRET'],
                   session['user'],
                   request.args.get('user', ''),
                   request.args.get('num', ''),
                   )
    return flask.render_template('download_data.html',
                                 ids='{}',
                                 **session["form_values"])


app.run()
