# -*- coding: utf-8 -*-
'''
maps server URIs to actions
'''

# core python imports

from glob import glob
import os
import time

# framework imports

from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_httpauth import HTTPTokenAuth
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse

# my app imports

from mjserver import app, db, BASE_DIR
from mjserver.errors import bad_request, error_response
from mjserver.forms import LoginForm, ProfileForm, RegistrationForm
from mjserver.models import Game, User, UsersGames


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


@app.route('/game/<game_id>')
@login_required
def view_game(game_id):
    ''' display info on a particular game '''
    this_game = Game.query.get(game_id)
    return render_template(
        'game.html',
        profiled=this_game,
        hands=this_game.get_score_table()
    )


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


@app.route('/user/<user_id>', methods=['GET', 'POST'])
@login_required
def view_profile(user_id):
    ''' display user profile page '''
    this_user = User.query.filter_by(id=user_id).first_or_404()
    form = ProfileForm(obj=this_user)
    if not form.validate_on_submit():
        return render_template('user.html', profiled=this_user, form=form)


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
        this_user = User()
        form.populate_obj(this_user)
        this_user.set_password(form.password.data)
        this_user.set_pin(form.pin.data)
        this_user.create_token()
        db.session.add(this_user)
        db.session.commit()
        flash('Congratulations, you are now a registered user, you are now logged in!')
        login_user(this_user)
        return redirect(url_for('view_profile', user_id=this_user.id))
    return render_template('register.html', title='Register', form=form)


#%%
API='/api/v0/'
token_auth = HTTPTokenAuth(scheme='Token')


@app.route(API + 'login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    try:
        user = User.query.filter_by(username=data['username']).first()
        if user.active and user.check_password(data['password']):
            login_user(user)
            response = jsonify({'id': user.id, 'token': user.token})
            response.status_code = 200
            return response
        else:
            msg = 'Invalid username/password combination'
    except Exception as e:
        msg = str(e)

    response = jsonify({'message': msg})
    response.status_code = 403
    return response


@app.route(API + 'game/new', methods=['POST'])
def receive_json():
    new_game = Game()

    data = request.get_json() or {}

    if 'desc' not in data or 'hands' not in data or 'players' not in data:
        return bad_request('must include username, email and pin fields')

    new_game.description = data['desc']
    new_game.started = ZZZ # TODO DateTime
    new_game.last_updated = ZZZ # TODO DateTime
    new_game.public = False
    new_game.log = data['log']
    new_game.json = ZZZ # TODO

    try:
        if 'final_score' in players:
            new_game.is_active = False
            scores = data['final_scores']
        else:
            new_game.is_active = True
            if 'scores' in data['hands'][-1]:
                scores = data['hands'][-1]['scores']
            else:
                scores = data['hands'][-2]['scores']
    except:
        scores = [0,0,0,0]

    players = []
    for idx in range(4):
        players[idx] = UsersGames(score=scores[idx], place=idx+1)
        try:
            a = User.query.get(1)
        except:
            a = User()
            a.username = 'new player'
            db.session.add(a)
        players[idx].player = a
        players[idx].game = new_game
        db.session.add(players[idx])

    db.session.commit()
    response = jsonify({'game.id': new_game.id})
    response.status_code = 201
    return response


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


@app.route(API + 'users', methods=['GET'])
@token_auth.login_required
def json_user_list():
    return jsonify(User.get_all_usernames())


@app.route(API + '/user/new', methods=['POST'])
def json_create_user():
    data = request.get_json() or {}

    if 'username' not in data or 'email' not in data or 'pin' not in data:
        return bad_request('must include username, email and pin fields')

    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return bad_request('%d Name already in use. Please use a different username' % existing_user.id)

    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return bad_request('%d Email address already in use. Please use a different email address' % existing_user.id)

    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()

    response = jsonify(user.to_dict())
    response.status_code = 201
    response.headers['user.id'] = user.id
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