# -*- coding: utf-8 -*-
'''
The database structure. flask db uses this to auto-generate the db.
And the server code uses this to operate the db.
Mostly the model part of MVC.
'''
import base64
from datetime import datetime, timedelta
from hashlib import md5
import os

from flask import g
from flask_login import UserMixin
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.collections import attribute_mapped_collection
from werkzeug.security import generate_password_hash, check_password_hash

from mjserver import db, login


#%% many-to-many mappings

#roles_users = db.Table(
#    'roles_users',
#    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
#    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
#    )

#users_teams = db.Table(
#    'users_teams',
#    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
#    db.Column('team_id', db.Integer(), db.ForeignKey('team.id'))
#    )

#games_teams = db.Table(
#    'games_teams',
#    db.Column('team_id', db.Unicode(255), db.ForeignKey('team.id')),
#    db.Column('game_id', db.Integer(), db.ForeignKey('game.id')),
#    db.Column('privilege', db.Integer(), db.ForeignKey('privilege.id'))
#    )


#%%


#class Role(db.Model):
#    ''' as yet unused. Intended for managing privileges '''
#    __tablename__ = 'role'
#    id = db.Column(db.Integer(), primary_key=True)
#    name = db.Column(db.String(80), unique=True)
#    description = db.Column(db.String(255))


#class Privilege(db.Model):
#    '''
#    not used yet, but intended to manage logged-in users' privileges
#    in reading/writing/deleting games.
#    '''
#    __tablename__ = 'privilege'
#    id = db.Column(db.Integer, primary_key=True)
#    description = db.Column(db.String(255))


#class Team(db.Model):
#    '''
#    As yet unused. Intended for grouping players into teams that share
#    the same privileges for managing games records, or appear in the same
#    competition or league. But none of that is written yet.
#    '''
#    __tablename__ = 'team'
#    id = db.Column(db.Integer, primary_key=True)
#    name = db.Column(db.Unicode(255))
#    description = db.Column(db.UnicodeText())
#    active = db.Column(db.Boolean())


class User(db.Model, UserMixin):
    '''
    Currently we work on the basis that every registered player has a login, and
    every registered login is a (potential) player. So this class is used
    both for players and for website logins.
    '''
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255))
    token_hash = db.Column(db.String(32), index=True)
    token_expiration = db.Column(db.DateTime)
    email = db.Column(db.Unicode(255), unique=True)
    username = db.Column(db.Unicode(255), unique=True)
    pin_hash = db.Column(db.String(32))
    password_hash = db.Column(db.String(128))
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(100))
    current_login_ip = db.Column(db.String(100))
    login_count = db.Column(db.Integer)
    active = db.Column(db.Boolean(), default=True)
    confirmed_at = db.Column(db.DateTime())

    games = association_proxy('played_games', 'game')
    scores = association_proxy('played_games', 'score')
    places = association_proxy('played_games', 'place')
    usersgames = db.relationship('UsersGames')

#    teams = db.relationship(
#        'Team',
#        secondary=users_teams,
#        primaryjoin=(users_teams.c.user_id == id),
#        backref=db.backref('members', lazy='dynamic'),
#        lazy='dynamic')

#
#    def add_to_team(self, team):
#        if not self.is_in_team(team):
#            self.teams.append(team)
#
#    def remove_from_team(self, team):
#        if self.is_in_team(team):
#            self.teams.remove(team)
#
#    def is_in_team(self, team):
#        return self.teams.filter(
#            users_teams.c.team_id == team.id).count() > 0

    def __repr__(self):
        ''' just for pretty printing '''
        return '<User {}>'.format(self.username)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @classmethod
    def get_all_usernames(cls, with_pin_hash=False):
        userlist = []
        query = db.session.query(cls.username).order_by(cls.username)
        if with_pin_hash:
            query = query.add_columns(cls.pin_hash)
        for value in query.all():
            userlist.append(value)
        return userlist

    def get_token(self, expires_in=60*60*24*35):
        '''
        issue an authentication token that lasts 35 days, and store it
        with the user in the database. Renew it if there's less than 28 days life
        left on it. This way, it will get renewed at most once per week, and
        user will remain logged in as long as they visit the site at least
        once every 28 days.
        '''
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds= 4 * expires_in/5):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        db.session.commit()
        return self.token

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def set_pin(self, pin):
        from mjserver.salt import HASH_SALT
        self.pin_hash = md5(bytes(str(pin), 'utf-8') + HASH_SALT).hexdigest()

    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    def to_dict(self):
        pass


@login.user_loader
def load_user(user_id):
    ''' not sure how this is used yet. I just copied it from the tutorial '''
    try:
        return User.query.get(int(user_id))
    except:
        return None


class Game(db.Model):
    '''
    The heart of the database: an individual game record
    '''
    __tablename__ = 'game'
    id = db.Column(db.Unicode(255), primary_key=True)
    description = db.Column(db.UnicodeText())
    json = db.Column(db.UnicodeText())
    log = db.Column(db.UnicodeText())
    public = db.Column(db.Boolean())
    started = db.Column(db.DateTime())
    last_updated = db.Column(db.DateTime())

    players = association_proxy('games_players', 'player')
    player_names = association_proxy('games_players', 'player.username')
    scores = association_proxy('games_players', 'score')
    places = association_proxy('games_players', 'place')
    usersgames = db.relationship('UsersGames')


#%% slowly working through this http://docs.sqlalchemy.org/en/latest/orm/extensions/associationproxy.html

class UsersGames(db.Model):
    ''' this maps users to games, and provides the score and placement '''
    __tablename = 'user_game'
    user_id = db.Column('user_id', db.Integer(), db.ForeignKey('user.id'), primary_key=True)
    game_id = db.Column('game_id', db.Unicode(255), db.ForeignKey('game.id'), primary_key=True)
    score = db.Column(db.Integer())
    place = db.Column(db.Integer())

    player = db.relationship(
        User,
        backref=db.backref('played_games', lazy='dynamic', cascade="all, delete-orphan")
    )

    game = db.relationship(
        Game,
        backref=db.backref(
            'games_players',
            lazy='immediate',
            cascade="all, delete-orphan",
            collection_class=attribute_mapped_collection("place"),
        ),
    )

    def __init__(self, user=None, game=None, score=-9999, place=-1):
        self.user = user
        self.game = game
        self.score = score
        self.place = place
