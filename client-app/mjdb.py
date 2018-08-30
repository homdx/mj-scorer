# -*- coding: utf-8 -*-
'''
database handling for ZAPS MJ Scorer
'''

from json import dumps, loads
import os
from pathlib import Path
import sqlite3

from kivy.app import App

class Mjdb():
    ''' database handling for archived, completed games '''

    __log = None
    cursor = None
    db = None


    def db_close(self):
        self.db.commit()
        self.db.close()


    def delete_game(self, key_to_delete):
        self.cursor.execute("DELETE FROM Games WHERE global_id=?", [key_to_delete])


    def does_game_exist(self, global_id):
        self.cursor.execute("SELECT COUNT(*) FROM Games WHERE global_id=?", [global_id])
        return self.cursor.fetchone()[0] > 0


    def init(self, filename='mj.sqlite'):
        app_root = App.get_running_app()
        self.__log = app_root.log
        fullpath = str(Path(app_root.user_data_dir) / filename)
        db_is_new = not os.path.exists(fullpath)
        self.db = sqlite3.connect(fullpath)
        self.cursor = self.db.cursor()
        if db_is_new:
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS Games(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                global_id TEXT,
                description TEXT,
                json TEXT);''')
            self.cursor.execute('CREATE UNIQUE INDEX idx_id ON Games (global_id);')
            self.cursor.execute('CREATE UNIQUE INDEX idx_desc ON Games (description);')


    def list_games(self):
        self.cursor.execute(
            "SELECT global_id, description, json FROM Games ORDER BY description DESC;")
        return self.cursor.fetchall()


    def load_game(self, global_id):
        self.cursor.execute("SELECT json FROM Games WHERE global_id=?", [global_id])
        return loads(self.cursor.fetchone()[0], encoding='utf8')


    def load_game_by_desc(self, desc):
        self.cursor.execute("SELECT json FROM Games WHERE description=?", [desc])
        return loads(self.cursor.fetchone()[0], encoding='utf8')


    def save_game(self, json, description):
        global_id = json['game_id']

        query = "UPDATE Games SET description=?, json=? WHERE global_id=?" \
            if self.does_game_exist(global_id) else \
            "INSERT INTO Games(description, json, global_id) VALUES (?,?,?)"

        self.cursor.execute(
            query,
            [description, dumps(json, ensure_ascii=False), global_id]
        )

        self.db.commit()
