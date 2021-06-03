import sys
import os
import flask
from flask import Flask, render_template, request, url_for, session,jsonify
from flask_session import Session
from flask_cors import CORS,cross_origin
import oauth2 as oauth
import urllib
import redis
import datetime
import requests


import tweepy as tw
from tweepy.auth import OAuthHandler
from tweepy.api import API

def to_log(*msg):
    for i in msg:
        print('************ ' + str(i))
    sys.stdout.flush()

def write_cache(key,item,dir_='oauth_store'):
    if session.get(dir_,None) is None:
        session[dir_] = {}
    session[dir_][key] = item


def date_to_id(date:str):
    return int(
        (datetime.datetime.strptime(date,"%Y-%m-%d").timestamp()-1288834975)*2**22*1000
    )


app = flask.Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

app.secret_key = "gs67hduyhw9nn7u"
app.config.from_object(__name__)
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
try:
    r = redis.from_url(os.environ.get("REDIS_URL"))
except ValueError:
    r = redis.Redis()
app.config['SESSION_REDIS'] = r
Session(app)


request_token_url = 'https://api.twitter.com/oauth/request_token'
access_token_url = 'https://api.twitter.com/oauth/access_token'
authorize_url = 'https://api.twitter.com/oauth/authorize'
show_user_url = 'https://api.twitter.com/1.1/users/show.json'


app.config['APP_CONSUMER_KEY'] = os.getenv(
    'CONSUMER_KEY', '-1')
app.config['APP_CONSUMER_SECRET'] = os.getenv(
    'CONSUMER_SECRET', '-1')
to_log('got env vars',app.config['APP_CONSUMER_KEY'][0]+app.config['APP_CONSUMER_SECRET'][0])
app.config['TEMPLATES_AUTO_RELOAD'] = False


@app.route('/')
@cross_origin()
def render_index():

    session["form_values"] = {"user":'',
                              "from":'',
                              "to":''
                              }
    session["extension_cursor"] = ''

    if session.get('user',None) is None:
        return flask.redirect(url_for('signin'))
    else:
        return flask.render_template('search.html', ids=jsonify([]),**session["form_values"])


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

    oauth_token = request.args.get('oauth_token')
    oauth_verifier = request.args.get('oauth_verifier')

    if oauth_token in session.get('oauth_store',{}):
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
    session['user'] = (real_oauth_token,real_oauth_token_secret)
    return flask.redirect(url_for('render_index'))


@app.route('/query')
def query():
    auth = OAuthHandler(app.config['APP_CONSUMER_KEY'], app.config['APP_CONSUMER_SECRET'])
    auth.set_access_token(*session['user'])

    user_name = request.args.get('user','')
    from_ = request.args.get('from','')
    to = request.args.get('to','')

    session["form_values"] = {"user":user_name,
                              "from":from_,
                              "to":to
                              }

    favorites_params = {"screen_name":user_name,
                        "count":20}
    if from_ != '':
        favorites_params["since"] = date_to_id(from_)
    if to != '':
        favorites_params["max_id"] = date_to_id(to)

    api = API(auth)
    results = api.favorites(**favorites_params)
    if len(results) != 0:
        session["extension_cursor"] = results[-1].id - 1
    else:
        session["extension_cursor"] = ''
    results_ids = []
    for tweet in results:
        results_ids.append(str(tweet.id))
    return flask.render_template('search.html', ids=jsonify(results_ids),**session["form_values"])


@app.route('/query/extend')
def query_extend():
    auth = OAuthHandler(app.config['APP_CONSUMER_KEY'], app.config['APP_CONSUMER_SECRET'])
    auth.set_access_token(*session['user'])

    user_name = session["form_values"]["user"]
    favorites_params = {"screen_name": user_name,
                        "count": 20}

    to = session["extension_cursor"]
    if to != '':
        favorites_params["max_id"] = to

    api = API(auth)
    results = api.favorites(**favorites_params)
    if len(results) != 0:
        session["extension_cursor"] = results[-1].id - 1
    else:
        session["extension_cursor"] = ''
    results_ids = []
    for tweet in results:
        results_ids.append(str(tweet.id))

    return flask.render_template('search.html', ids=jsonify(results_ids),**session["form_values"])


@app.route('/get_tweet_html')
def get_tweet_html():
    link = request.args.get("url")
    to_log(link)
    return requests.get(link).json()


if __name__ == '__main__':
    app.run()

