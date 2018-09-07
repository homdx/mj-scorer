# -*- coding: utf-8 -*-
'''
database handling for ZAPS MJ Scorer
'''

from json import dumps, loads
import os
from pathlib import Path
import sqlite3
import threading
import time

import requests

from kivy.app import App
from kivy.network.urlrequest import UrlRequest


class Mjio():
    '''
    this class does ALL the server communication in a separate thread
    https://github.com/kivy/kivy/wiki/Working-with-Python-threads-inside-a-Kivy-application
    '''
    __current_game = None
    __iothread = None
    __requests = {}
    __responses = []
    __save_callbacks = []
    __seq_id = 0
    __do_at_once = 4

    api_path = 'https://mj.bacchant.es/api/v0/'
    current_game_id = None
    cursor = None
    db = None
    games = []
    kill = False
    session = None
    syncdb = False
    update_interval = 300  # seconds
    update_server = False

    def __init__(self, **kwargs):
        super(Mjio, self).__init__(**kwargs)

        # start iothread

        self.__iothread = threading.Thread(target=self.__io_looper)
        self.__iothread.daemon = True
        self.__iothread.start()


    def __do_callbacks(self, response):
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
        self.__seq_id += 1
        return 'T%s-%f' % (self.__seq_id, time.time())


    def __io_looper(self, *args):
        '''

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
                    response = requests.post(url=self.api_path,
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
        ''' add a request for server communications '''
        self.__requests[self.__get_unique_id()] = {
            'callback': callback,
            'payload': payload,
            'retry': retry_after_restart}


    def get_game_list(self, filters, callback):
        '''
        '''
        callback(None)


    def get_game(self, game_id, callback):
        '''
        '''
        callback(None)

    def post_game(self, jsonstring):
        req = UrlRequest(
            url='https://mj.bacchant.es/api/v0/game',
            on_success=self.call_ok,
            on_redirect=self.call_fail,
            on_failure=self.call_fail,
            on_error=self.call_fail,
            req_body=jsonstring.encode('utf-8'),
            req_headers={'Content-type':  'application/json',
                         'Authorization': App.get_running_app().auth_token},
            timeout=30,
            method='POST',
            #wait=wait
        )

        self.games_to_sync.append(req)


    def sync_games(self):
        self.cursor.execute(
            "SELECT global_id, json FROM Games WHERE on_server=0;")
        return self.cursor.fetchall()


    def sync_now(self):
        return False # TODO
        self.__requests.sync()


class Mjdb():
    ''' database handling for archived, completed games '''

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
        if self.db is not None:
            return
        app_root = App.get_running_app()
        self.__log = app_root.log
        fullpath = str(Path(app_root.user_data_dir) / filename)
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
        self.cursor.execute("SELECT json FROM Games WHERE global_id=?", [global_id])
        return loads(self.cursor.fetchone()[0], encoding='utf8')


    def load_game_by_desc(self, desc):
        self.cursor.execute("SELECT json FROM Games WHERE description=?", [desc])
        result = self.cursor.fetchone()
        return None if result is None else loads(result[0], encoding='utf8')


    def save_game(self, json, description, wait=False):
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
