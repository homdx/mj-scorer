# -*- coding: utf-8 -*-
'''
The database structure. flask db uses this to auto-generate the db.
And the server code uses this to operate the db.
Mostly the model part of MVC.
'''
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from mjserver import db, login


#%% many-to-many mappings

#roles_users = db.Table(
#    'roles_users',
#    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
#    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
#    )

users_teams = db.Table(
    'users_teams',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('team_id', db.Integer(), db.ForeignKey('team.id'))
    )

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


class Team(db.Model):
    '''
    As yet unused. Intended for grouping players into teams that share
    the same privileges for managing games records, or appear in the same
    competition or league. But none of that is written yet.
    '''
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255))
    description = db.Column(db.UnicodeText())
    active = db.Column(db.Boolean())


class User(db.Model, UserMixin):
    '''
    Currently we work on the basis that every registered player has a login, and
    every registered login is a (potential) player. So this class is used
    both for players and for website logins.
    '''
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Unicode(255), unique=True)
    username = db.Column(db.Unicode(255), unique=True)
    password_hash = db.Column(db.String(128))
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(100))
    current_login_ip = db.Column(db.String(100))
    login_count = db.Column(db.Integer)
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())

    teams = db.relationship(
        'Team',
        secondary=users_teams,
        primaryjoin=(users_teams.c.user_id == id),
        backref=db.backref('members', lazy='dynamic'),
        lazy='dynamic')

    def add_to_team(self, team):
        if not self.is_in_team(team):
            self.teams.append(team)

    def remove_from_team(self, team):
        if self.is_in_team(team):
            self.teams.remove(team)

    def is_in_team(self, team):
        return self.teams.filter(
            users_teams.c.team_id == team.id).count() > 0

    def __repr__(self):
        ''' just for pretty printing '''
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


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


#%%


class UsersGames(db.Model):
    ''' this maps users to games, and provides the score and placement '''
    __tablename = 'users_games'
    user_id = db.Column('user_id', db.Integer(), db.ForeignKey('user.id'), primary_key=True)
    game_id = db.Column('game_id', db.Unicode(255), db.ForeignKey('game.id'), primary_key=True)
    score = db.Column(db.Integer())
    place = db.Column(db.Integer())
    user = db.relationship(
        User,
        backref=db.backref('games', lazy='dynamic')
        )
    game = db.relationship(
        Game,
        backref=db.backref('players', lazy='immediate'),
        order_by='asc(place)')
