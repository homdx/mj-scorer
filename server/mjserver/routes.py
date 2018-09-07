# -*- coding: utf-8 -*-
'''
maps server URIs to actions. Mostly the Controller part of MVC.
'''

from glob import glob
from hashlib import md5
import os
import pickle
import random
import time

from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_httpauth import HTTPTokenAuth
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse

from mjserver import app, db, BASE_DIR
from mjserver.errors import bad_request, error_response
from mjserver.forms import LoginForm, RegistrationForm
from mjserver.models import Game, User
from mjserver.salt import HASH_SALT

with open(str(BASE_DIR / 'wordlist.pickle'), 'rb') as wordlist_file:
    wordlist = pickle.load(wordlist_file)
wordlist_len = len(wordlist)

@app.route('/')
def front_page():
    '''
    serve the site front page, which is currently the only place that the
    mobile app can be downloaded from. So we dynamically see which
    version of the app is most recent, extract the version number from the
    filename, and offer that to the browser.
    '''
    test_dir = BASE_DIR / 'static'
    files = glob(str(test_dir / '*.apk'))
    try:
        newest = files[0][1+len(str(test_dir)):]
        version = newest.split('-')[1]
        filetime = time.strftime('%Y-%m-%d %H:%M', time.gmtime(os.path.getmtime(files[0])))
    except:
        newest = 'None available currently'
        version = '?'
        filetime = '?'

    return render_template(
        'front_page.html',
        version=version,
        filetime=filetime,
        newest=newest,
        user=current_user)


@app.route('/user/<user_id>')
@login_required
def view_profile(user_id):
    ''' display user profile page '''
    this_user = User.query.filter_by(id=user_id).first_or_404()
    return render_template('user.html', profiled=this_user)


@app.route('/game/<game_id>')
@login_required
def view_game(game_id):
    ''' display info on a particular game '''
    this_game = Game.query.get(game_id)
    return render_template('game.html', profiled=this_game)


@app.route('/privacy')
def privacy():
    ''' display site privacy policy '''
    return render_template('privacy.html')


@app.route('/download-my-details')
@login_required
def dump_my_data():
    ''' TODO provide GDPR-compliant data dump of a user's data '''
    return "Coming soon. Once we've got some data for you"


@app.route('/games/')
def games_index():
    ''' TODO list of games viewable by current user '''
    return 'games_index'


@app.route('/get-token')
@login_required
def get_token():
    ''' provide random 4-word sequence for logins '''
    token = ''
    sep = ''
    for idx in random.sample(range(wordlist_len), 4):
        token += sep + wordlist[idx]
        sep = ' '
    return token


@app.route('/login', methods=['GET', 'POST'])
def login():
    ''' handle website logins '''
    if current_user.is_authenticated:
        return redirect(url_for('front_page'))
    form = LoginForm()
    if form.validate_on_submit():
        this_user = User.query.filter_by(username=form.username.data).first()
        if this_user is None \
                or not this_user.check_password(form.password.data) \
                or not this_user.active:
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(this_user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('front_page')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    ''' log current user out '''
    logout_user()
    return redirect(url_for('front_page'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    ''' register a new user '''
    if current_user.is_authenticated:
        return redirect(url_for('front_page'))
    form = RegistrationForm()
    if form.validate_on_submit():
        this_user = User(username=form.username.data, email=form.email.data)
        this_user.set_password(form.password.data)
        this_user.set_pin(form.pin.data)
        db.session.add(this_user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


#%%
API='/api/v0/'
token_auth = HTTPTokenAuth()


@app.route(API + 'game', methods=['POST'])
def receive_json():
    with open(str(BASE_DIR / 'sent.json'), 'w') as f:
        f.write(str(request.get_json()))
    return 'post received!'


@token_auth.verify_token
def verify_token(token):
    test = User.check_token(token) if token else None

    if test is not None and test.active:
        login_user(test)
        return True
    return False


@token_auth.error_handler
def token_auth_error():
    return error_response(401)


@app.route(API + 'usersmd5', methods=['GET'])
def json_usermd5_list():
    userlist = []
    for value in User.get_all_usernames():
       userlist.append(md5(bytes(value[0], 'utf-8') + HASH_SALT).hexdigest())
    return jsonify(userlist)


@app.route(API + 'users', methods=['GET'])
#@token_auth.login_required
def json_user_list():
    return jsonify(User.get_all_usernames(True))


@app.route(API + '/user/new', methods=['POST'])
def json_create_user():
    data = request.get_json() or {}
    if 'username' not in data or 'email' not in data or 'pin_hash' not in data:
        return bad_request('must include username, email and pin fields')
    if User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')
    if User.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address')
    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    response = jsonify(user.to_dict())
    response.status_code = 201
    response.headers['new_id'] = user.id
    response.headers['token'] = user.get_token()
    return response
#
#@app.route(API + '/user/<int:id>', methods=['PUT'])
#def json_update_user(id):
#    pass

@app.route(API + '/game/new', methods=['POST'])
@token_auth.login_required
def json_create_game():
    pass


@app.route(API + '/game/<int:id>', methods=['PUT'])
@token_auth.login_required
def json_update_game(id):
    pass