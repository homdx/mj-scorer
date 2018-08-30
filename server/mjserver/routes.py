# -*- coding: utf-8 -*-
'''
maps server URIs to actions. Mostly the Controller part of MVC.
'''

from glob import glob
import os
import time

from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse

from mjserver import app, db, BASE_DIR
from mjserver.forms import LoginForm, RegistrationForm
from mjserver.models import User


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
def user(user_id):
    ''' display user profile page '''
    this_user = User.query.filter_by(id=user_id).first_or_404()
    games = [
        {'id': 1,
         'description': 'game 1',
         'p1': user.username, 'p2': 'Groucho', 'p3': 'Harpo', 'p4': 'Chico'},
        {'id': 2,
         'description': 'game 2',
         'p1': 'Groucho', 'p2': 'Zeppo', 'p3': user.username, 'p4': 'Gummo'},
    ]
    return render_template('user.html', user=this_user, games=games)


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


@app.route('/login', methods=['GET', 'POST'])
def login():
    ''' handle website logins '''
    if current_user.is_authenticated:
        return redirect(url_for('front_page'))
    form = LoginForm()
    if form.validate_on_submit():
        this_user = User.query.filter_by(username=form.username.data).first()
        if this_user is None or not this_user.check_password(form.password.data):
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
        db.session.add(this_user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)
