# flask-security? something oauth?

import inspect
import os
import sys

from flask import Flask, jsonify
from authlib.flask.client import OAuth
from loginpass import create_flask_blueprint
from loginpass import ( Discord, Google,
    # Facebook, StackOverflow, GitHub, Slack,
    # Twitter, Reddit, Gitlab, Dropbox,
    # Bitbucket, Spotify, Strava
)

cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(
    inspect.currentframe() ))[0]))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

from front_page import front_page

OAUTH_BACKENDS = [ Discord, Google,
    # Twitter, Facebook, GitHub, Dropbox,
    # Reddit, Gitlab, Slack, StackOverflow,
    # Bitbucket, Strava, Spotify
]

application = Flask(__name__)
application.config.from_pyfile('config.py')
oauth = OAuth(application)

@application.route('/')
def fp():
    return front_page()

@application.route('/hid/')
def index():
    tpl = '<li><a href="/{}/login">{}</a></li>'
    lis = [tpl.format(b.OAUTH_NAME, b.OAUTH_NAME) for b in OAUTH_BACKENDS]
    return '<ul>{}</ul>'.format(''.join(lis))


def handle_authorize(remote, token, user_info):
    # type(remote) == RemoteApp
    return str(token)  + '<hr>' + str(user_info)


for backend in OAUTH_BACKENDS:
    bp = create_flask_blueprint(backend, oauth, handle_authorize)
    application.register_blueprint(bp, url_prefix='/{}'.format(backend.OAUTH_NAME))


@application.route('/group/1')
def boo():
    return 'Boo!'

