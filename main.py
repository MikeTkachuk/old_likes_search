import sys
import os
import flask
from flask import Flask, render_template, request, url_for, session
from flask_session import Session
import oauth2 as oauth
import urllib
import redis
import datetime

import tweepy as tw
from tweepy.auth import OAuthHandler
from tweepy.api import API

def to_log(*msg):
    for i in msg:
        print('************ ' + i)
    sys.stdout.flush()

def write_cache(key,item,dir_='oauth_store'):
    if session.get(dir_,None) is None:
        session[dir_] = {}
    session[dir_][key] = item


def date_to_id(date:str):
    return int(
        datetime.datetime.strptime(date,"%d/%m/%y").timestamp()*2**(64-41)
    )


app = flask.Flask(__name__)

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



@app.route('/')
def render_index():
    with open('/app/templates/results.html','w') as f:
        f.write('')
    if session.get('user',None) is None:
        return flask.redirect(url_for('signin'))
    else:
        return flask.render_template('search.html',results='results.html')


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

    user_name = request.args.get('user')
    from_ = date_to_id(request.args.get('from',None))
    to = date_to_id(request.args.get('to',None))
    count = request.args.get('count',None)

    api = API(auth)
    results = api.favorites(screen_name=user_name,count=count,since=from_,max_id=to)
    results_html = []
    for tweet in results:
        tweet_url = f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}"
        to_log(tweet_url)
        results_html.append(api.get_oembed(url=tweet_url)["html"])
    with open('/app/templates/results.html','w') as f:
        for i in results_html:
            f.write(i)
            f.write(' ')

    return flask.render_template('search.html',results='results.html')


if __name__ == '__main__':
    app.run()

