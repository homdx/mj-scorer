# -*- coding: utf-8 -*-
'''
Database-handling. This receives games as json, and stores
them in the database. In time, this module will also handle the server communications,
in a separate thread. Only back-end stuff is in here, no UI.

Mjio makes sync/async network requests
Mjdb does local database queries
'''

from json import dumps, loads
import os
from pathlib import Path
import pickle
import sqlite3
import threading
import time

import requests

from kivy.app import App
from kivy.network.urlrequest import UrlRequest


class Mjio():
    '''
    this class does ALL the server communication (eventually, in a separate thread)
    https://github.com/kivy/kivy/wiki/Working-with-Python-threads-inside-a-Kivy-application
    '''
    __api_path = 'http://localhost:5000/api/v0/' # 'https://mj.bacchant.es/api/v0/'
    __current_game = None
    __do_at_once = 4
    __iothread = None
    __requests = {}
    __responses = []
    __save_callbacks = []
    __seq_id = 0
    __token = ''

    current_game_id = None
    cursor = None
    db = None
    games = []
    kill = False
    session = None
    syncdb = False
    update_interval = 300  # seconds
    update_server = False

    def __init__(self, token=None, server_path=None, **kwargs):
        super(Mjio, self).__init__(**kwargs)

        if token is not None:
            self.set_token(token)

        if server_path is not None:
            self.set_server(server_path)

        return
        # start iothread

        self.__iothread = threading.Thread(target=self.__io_looper)
        self.__iothread.daemon = True
        self.__iothread.start()


    def __do_callbacks(self, response):
        ''' currently unused '''
        print(response.text)
        results = loads(response.content, encoding='utf8')
        for idx in results['acknowledged']:
            try:
                if self.__requests[idx]['callback'] is not None:
                    callback = self.__requests[idx]['callback']
                    try:
                        args = response[idx]
                    except:
                        args = None
                    callback(args)
                del self.__requests[idx]
            except KeyError:
                pass # it's ok to have not received this


    def __get_unique_id(self):
        ''' currently unused '''
        self.__seq_id += 1
        return 'T%s-%f' % (self.__seq_id, time.time())


    def __io_looper(self, *args):
        '''
        currently unused
        this is the thread call that talks to the server
         '''

        self.session = requests.Session()

        # now just hang around waiting for entries in self.log_stack and self.requests

        while not self.kill:

            time.sleep(self.update_interval - 2)

            if self.syncdb:
                self.sync_now()

            if self.__requests and self.update_server:


                print('preparing to talk to server')
                requests_to_send = {}
                self.__responses = []

                for key, value in self.__requests.items():
                    requests_to_send[key] = value['payload']

                jsondata = dumps(requests_to_send, ensure_ascii=False).encode('utf8')
                try:
                    response = requests.post(url=self.__api_path,
                                             data=jsondata,
                                             headers={'Content-Type': 'application/json'})

                    if response.ok:
                        self.__do_callbacks(response.content)
                    else:
                        print('error, status=%d' % response.status_code)

                except IOError:
                    # nothing remarkable - we expect to go offline sometimes
                    pass

                self.__requests.sync()

        self.__requests.close()


    def add_request(self, payload, callback=None, retry_after_restart=True):
        '''
        currently unused
        add a request for server communications
        '''
        self.__requests[self.__get_unique_id()] = {
            'callback': callback,
            'payload': payload,
            'retry': retry_after_restart}


    def authenticate(self, username, password):
        '''
        get authentication token from server, using username and password
        '''
        try:
            req = requests.post(
                url=self.__api_path + 'login',
                json={'username': username, 'password': password},
                )
            if req.ok:
                self.__token = req.json()['token']
                return req.json()
            else:
                err = req.json()['message']
        except Exception as e: # ConnectionError means server unavailable
            err = str(e)
        self.__token = ''
        return {'token': '', 'message': err}


    def get_game_list(self, filters, callback):
        '''
        currently unused
        '''
        callback(None)


    def get_game(self, game_id, callback):
        '''
        currently unused
        '''
        callback(None)


    def get_users(self, cache=['use']):
        '''
        get list of users from server (and cache locally); if network unavailable, use cache
        '''
        fullpath = str(Path(App.get_running_app().user_data_dir) / 'users.pickle')
        if 'clear' in cache:
            with open(fullpath, 'wb') as f:
                pickle.dump([], f, protocol=4)

        try:
            req = requests.get(
                url=self.__api_path + 'users',
                headers={'Authorization': 'Token %s' % self.__token},
                )
            if req.ok:
                userlist = req.json()
                with open(fullpath, 'wb') as f:
                    pickle.dump(userlist, f, protocol=4)
                return userlist
        except Exception as e:
            msg = str(e)

        if 'use' in cache:
            try:
                with open(fullpath, 'rb') as f:
                    userlist = pickle.load(f)
                return userlist
            except:
                pass

        return []


    def has_token(self):
        '''
        check whether a token exists: NB doesn't check whether it's valid
        '''
        return self.__token != ''


    def post_game(self, dict_to_post):
        req = requests.post(
            url=self.__api_path + 'game/new',
            json=dict_to_post,
            headers={
                'Authorization': 'Token %s' % self.__token,
                # 'Content-Type': 'application/json;charset=UTF-8' # shouldn't be needed
            },
        )
        return req


    def post_game_async(self, jsonstring):
        ''' currently unused '''
        req = UrlRequest(
            url=self.__api_path+'game',
            on_success=self.call_ok,
            on_redirect=self.call_fail,
            on_failure=self.call_fail,
            on_error=self.call_fail,
            req_body=jsonstring.encode('utf-8'),
            req_headers={'Content-type':  'application/json',
                         'Authorization': self.__token},
            timeout=30,
            method='POST',
            #wait=wait
        )

        self.games_to_sync.append(req)


    def set_server(self, server):
        ''' build api path from server path '''
        self.__api_path = server + ('' if server[-1] == '/' else '/') + 'api/v0/'

    def set_token(self, token):
        '''
        currently unused: set the token used for authentication
        '''
        self.__token = token


    def sync_games(self):
        ''' currently unused '''
        self.cursor.execute(
            "SELECT global_id, json FROM Games WHERE on_server=0;")
        return self.cursor.fetchall()


    def sync_now(self):
        ''' currently unused '''
        return False # TODO
        self.__requests.sync()


class Mjdb():
    ''' database handling for archived, completed games '''

    __io = None
    __log = None
    cursor = None
    db = None
    games_to_sync = {}


    def db_close(self):
        self.db.commit()
        self.db.close()


    def delete_game(self, key_to_delete):
        self.cursor.execute("DELETE FROM Games WHERE global_id=?", [key_to_delete])


    def does_game_exist(self, global_id):
        self.cursor.execute("SELECT COUNT(*) FROM Games WHERE global_id=?", [global_id])
        return self.cursor.fetchone()[0] > 0


    def init(self, filename='mj.sqlite'):
        ''' initialisation of the database done once the app is initialised '''
        if self.db is not None:
            return
        app = App.get_running_app()
        self.__log = app.log
        fullpath = str(Path(app.user_data_dir) / filename)
        #os.remove(fullpath)
        db_is_new = not os.path.exists(fullpath)
        self.db = sqlite3.connect(fullpath)
        self.cursor = self.db.cursor()
        if db_is_new:
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS Games(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ongoing BOOLEAN DEFAULT 1,
                global_id TEXT,
                description TEXT,
                json TEXT,
                on_server BOOLEAN DEFAULT 0);''')
            self.cursor.execute('CREATE UNIQUE INDEX idx_id ON Games (global_id);')
            self.cursor.execute('CREATE UNIQUE INDEX idx_desc ON Games (description);')


    def list_games(self, ongoing=None):
        ''' get list of games from local db, optionally only the ongoing ones '''
        if ongoing is None:
            self.cursor.execute(
                "SELECT global_id, description, json FROM Games ORDER BY description DESC;"
                )
        else:
            self.cursor.execute(
                "SELECT global_id, description, json FROM Games WHERE ongoing=? ORDER BY description DESC;",
                [ongoing])

        return self.cursor.fetchall()


    def load_game(self, global_id):
        ''' unused as yet '''
        self.cursor.execute("SELECT json FROM Games WHERE global_id=?", [global_id])
        return loads(self.cursor.fetchone()[0], encoding='utf8')


    def load_game_by_desc(self, desc):
        ''' unused as yet '''
        self.cursor.execute("SELECT json FROM Games WHERE description=?", [desc])
        result = self.cursor.fetchone()
        return None if result is None else loads(result[0], encoding='utf8')


    def save_game(self, json, description, wait=False):
        ''' saves game to local database '''
        global_id = json['game_id']

        query = "UPDATE Games SET description=?, json=?, ongoing=? WHERE global_id=?" \
            if self.does_game_exist(global_id) else \
            "INSERT INTO Games(description, json, ongoing, global_id) VALUES (?,?,?,?)"

        jsonstring = dumps(json, ensure_ascii=False)
        self.cursor.execute(
            query,
            [description, jsonstring, json['in_progress'], global_id]
            )
        self.db.commit()


    def set_io(self, obj):
        ''' unused as yet '''
        self.__io = obj