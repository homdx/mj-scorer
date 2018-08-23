# -*- coding: utf-8 -*-
'''

class for both live and completed games

'''

from datetime import datetime
from pathlib import Path

from time import time

from kivy.app import App
from kivy.properties import ListProperty, NumericProperty
from kivy.storage.jsonstore import JsonStore
from kivy.uix.boxlayout import BoxLayout

from mjdb import Mjdb
from mjenums import Log, Rules


class MjGameStatus(BoxLayout):
    ''' class for game in progress, and completed games '''
    __db = Mjdb()

    __hand_count = 0

    __game_dict = {}

    __json_path = None

    __saved_game_attributes = [
        'game_id', 'start_time', 'in_progress']

    __start_of_hand_attributes = [
        'round_wind_index', 'dealership', 'hand_redeals']

    __end_of_hand_attributes = [
        'riichi_sticks', 'honba_sticks', ]

    __score_table = None

    dealership = NumericProperty(1)
    game_id = ''
    game_log = ListProperty([])
    hand_redeals = NumericProperty(0)
    honba_sticks = NumericProperty(0)
    in_progress = False
    riichi_sticks = NumericProperty(0)
    riichi_delta_this_hand = [0, 0, 0, 0]
    round_wind_index = NumericProperty(0)
    rules = None
    start_time = NumericProperty(0)


    def end_of_game(self):
        self.__end_of_hand()


    def erase(self):
        self.__game_dict['current'] = {}
        self.sync()


    def fill_games_table(self):
        app_root = App.get_running_app()
        table = app_root.root.ids.games_table
        table.data_items = []
        try:
            games_list = self.__db.list_games()
            for game in games_list:
                table.data_items.append(game[1])
        except:
            pass


    def forget_last_hand(self, do_it):
        ''' restore game state to hand before last; remove last hand '''
        if not do_it:
            return True
        app_root = App.get_running_app()
        app_root.log(Log.UNUSUAL, 'Forget last hand')
        was_not_redeal = not self.hand_redeals
        if self.__restore_row(-2):
            app_root.set_headline('Last hand forgotton')
            if was_not_redeal:
                # rotate winds backwards only if the hand to be forgotten
                #   was NOT a dealer-continuation hand
                players = app_root.players
                lastwind = players[0].wind
                for player in range(3):
                    players[player].wind = players[player + 1].wind
                players[3].wind = lastwind
                app_root.animate_winddiscs('clockwise')

            self.__score_table.delete_row(-1)
            self.__game_dict['current']['hands'].pop()
            self.__hand_count = len(self.__game_dict['current']['hands']) - 1
            self.sync()
            self.__score_table.update_scores()
            app_root.popup_menu.ids['forgetlasthandbutton'].disabled = self.__hand_count == 1
        return True


    def game_summary(self):
        description = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' + (
            self.ids.hand_number.text if self.in_progress else '(ended)'
            ) + ': '

        app_root = App.get_running_app()
        for idx in range(4):
            description += '%s(%s), '% (
                self.__game_dict['current']['players'][idx],
                '%.1f' % ((
                    app_root.players[idx].score if self.in_progress else
                    self.__game_dict['current']['final_score'][idx]
                    ) / 10)
            )
        return description


    def load(self, game):
        ''' load a game restored from the db '''
        self.__rebuild_score_table()
        self.__restore_row(-1)
        # TODO player_names etc


    def load_game_by_desc(self, desc):
        try:
            self.__game_dict['current'] = self.__db.load_game_by_desc(desc)
            self.resume()
            App.get_running_app().screen_switch('scoresheet')
        except:
            # TODO failed to load game from db
            pass


    def next_hand(self):
        self.__end_of_hand()
        self.__next_hand()


    def resume(self, do_resume=True):
        ''' if user has requested resumption,
        set the game state to the most recent one in the current game_dict
        '''
        app_root = App.get_running_app()

        if not do_resume:
            self.__reset()
            return False

        self.__score_table = app_root.root.ids.score_table

        if not self.__restore_row(-1):
            app_root.log(Log.ERROR, 'Failed to restore game')
            return False

        app_root.log(Log.DEBUG, 'Restoring game')

        for item in self.__saved_game_attributes:
            setattr(self, item, self.__game_dict['current'][item])

        self.rules = Rules(self.__game_dict['current']['rules'])
        self.__rebuild_score_table()
        app_root.toggle_buttons()
        app_root.screen_switch('hand')

        windlist = app_root.winds + app_root.winds + app_root.winds
        for idx in range(4):
            app_root.players[idx].player_name = \
                app_root.root.ids['player%dname' % idx].text = \
                self.__game_dict['current']['players'][idx]
            app_root.players[idx].index = idx
            app_root.players[idx].wind = windlist[5 + idx - self.dealership]

        app_root.popup_menu.ids['forgetlasthandbutton'].disabled = \
            not self.in_progress or self.__hand_count < 2

        return True


    def resumption_possible(self):
        ''' when starting up, check if there's a partial game in progress
        stored, and if so, resume it automatically
        '''
        app_root = App.get_running_app()
        self.__db.init()
        self.__json_path = str(Path(app_root.user_data_dir) / 'current_game.json')
        try:
            self.__game_dict = JsonStore(self.__json_path)
            if self.__game_dict['current']['in_progress']:
                return True
        except:
            pass
        return False


    def save(self, results={}):
        ''' save the game to the games database'''
        self.__game_dict['current'].update(results)
        self.__game_dict['current']['in_progress'] = self.in_progress
        description = self.game_summary()
        self.__db.save_game(self.__game_dict['current'], description)


    def start(self, ruleset=None, names=None):
        ''' initialise all variables for a new game '''

        app_root = App.get_running_app()

        self.__reset()
        self.rules = Rules(ruleset)
        for item in self.__saved_game_attributes:
            self.__game_dict['current'][item] = getattr(self, item)

        self.__game_dict['current']['players'] = \
            ['player1', 'player2', 'player3', 'player4'] \
            if names is None else names

        for idx in range(4):
            app_root.riichi_stick_refs[idx].visible = 0

        self.__game_dict['current']['rules'] = ruleset
        self.__game_dict['current']['start'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.__game_dict['current']['hands'] = [{'scores': [self.rules.starting_points] * 4}]
        self.next_hand()
        app_root.toggle_buttons()


    def sync(self):
        self.__game_dict.put('updated', updated=True)


    def update_score(self, data_row, new_section):
        scores = self.__score_table.add_row(data_row, new_section)
        self.__game_dict['current']['hands'][self.__hand_count]['deltas'] = data_row
        self.__game_dict['current']['hands'][self.__hand_count]['scores'] = scores


    def __end_of_hand(self):
        for attr in self.__end_of_hand_attributes:
            self.__game_dict['current']['hands'][self.__hand_count][attr] = getattr(self, attr)


    def __next_hand(self):
        self.__game_dict['current']['hands'].append({})
        self.__hand_count = len(self.__game_dict['current']['hands']) - 1
        self.riichi_delta_this_hand = 4 * [0]
        for attr in self.__start_of_hand_attributes:
            self.__game_dict['current']['hands'][self.__hand_count][attr] = getattr(self, attr)
        self.sync()


    def __rebuild_score_table(self):
        self.__score_table.reset()
        self.__score_table.column_headings[1:] = self.__game_dict['current']['players']
        self.__score_table.starting_points = self.rules.starting_points
        for hand in self.__game_dict['current']['hands']:
            if 'deltas' in hand:
                self.__score_table.add_row(
                    hand['deltas'],
                    hand['dealership'] == 1 and hand['hand_redeals'] == 0
                )
        # if there are results, use them
        if 'net_scores' in self.__game_dict['current']:
            self.__score_table.ids.net_scores.data_items[1:] = \
                self.__game_dict['current']['net_scores']
        if 'uma' in self.__game_dict['current']:
            self.__score_table.ids.scoretable_uma.data_items[1:] = \
                self.__game_dict['current']['uma']
        if 'chombos' in self.__game_dict['current']:
            self.__score_table.ids.scoretable_chombos.data_items[1:] = \
                self.__game_dict['current']['chombos']
        if 'adjustments' in self.__game_dict['current']:
            self.__score_table.ids.scoretable_adjustments.data_items[1:] = \
                self.__game_dict['current']['adjustments']
        if 'final_score' in self.__game_dict['current']:
            self.__score_table.ids.scoretable_final_totals.data_items[1:] = \
                self.__game_dict['current']['final_score']

    def __reset(self):
        app_root = App.get_running_app()

        self.__score_table = app_root.root.ids.score_table
        self.__score_table.reset()
        self.__game_dict = JsonStore(self.__json_path)
        self.__game_dict['current'] = {}

        self.__hand_count = 0
        self.dealership = 1
        self.game_id = app_root.config.get('main', 'installation_id') + str(int(self.start_time))
        self.game_log = []
        self.hand_redeals = 0
        self.honba_sticks = 0
        self.in_progress = True
        self.riichi_sticks = 0
        self.round_wind_index = 0
        self.start_time = time()


    def __restore_row(self, row=-2):
        app_root = App.get_running_app()
        try:
            last_row = self.__game_dict['current']['hands'][row]
            previous_row = self.__game_dict['current']['hands'][row - 1]

            for attr in self.__start_of_hand_attributes:
                setattr(self, attr, last_row[attr])

            for attr in self.__end_of_hand_attributes:
                setattr(self, attr, previous_row[attr])

            for idx in range(4):
                app_root.players[idx].score = previous_row['scores'][idx]

            self.__hand_count = len(self.__game_dict['current']['hands']) - 1
            self.riichi_delta_this_hand = 4 * [0]

            return True

        except Exception as err:
            app_root.log(
                Log.ERROR,
                "Failed to restore hand %d: %s" % (row, str(err))
                )
            app_root.set_headline('Failed to delete last hand')
            return False


    @staticmethod
    def get_kv():
        return '''

<HonbaStick@Widget>:

    canvas:

        Color:
            rgba: 1., 1., 1., 1.
        Line:
            width: self.width / 2
            points: [self.right - self.width/2, self.y + self.width / 2, self.right - self.width/2, self.top - self.width / 2]

        Color:
            rgba: 0., 0., 0., 1
        Ellipse:
            size: self.width/3, self.width/3
            pos: self.right - 4. * self.width / 10., self.y + 3. * self.height / 9.
        Ellipse:
            size: self.width/3, self.width/3
            pos: self.right - 4. * self.width / 10., self.y + 4. * self.height / 9.
        Ellipse:
            size: self.width/3, self.width/3
            pos: self.right - 4. * self.width / 10., self.y + 5. * self.height / 9.
        Ellipse:
            size: self.width/3, self.width/3
            pos: self.right - 4. * self.width / 10., self.y + 6. * self.height / 9.
        Ellipse:
            size: self.width/3, self.width/3
            pos: self.right - 9. * self.width / 10., self.y + 3. * self.height / 9.
        Ellipse:
            size: self.width/3, self.width/3
            pos: self.right - 9. * self.width / 10., self.y + 4. * self.height / 9.
        Ellipse:
            size: self.width/3, self.width/3
            pos: self.right - 9. * self.width / 10., self.y + 5. * self.height / 9.
        Ellipse:
            size: self.width/3, self.width/3
            pos: self.right - 9. * self.width / 10., self.y + 6. * self.height / 9.


<SmallRiichiStick@Widget>:
    canvas:
        Color:
            rgba: .3, .3, 1., 1
        Line:
            width: self.width/2
            points: [self.right - self.width/2, self.y + self.width/2, self.right - self.width/2, self.y + self.height - self.width/2]
        Color:
            rgba: 1., 1., 1., 1
        Ellipse:
            size: self.width/2, self.width/2
            pos: self.center_x-self.width/4, self.center_y-self.width/4


<MjGameStatus>:
    orientation: 'vertical'
    size_hint: 0.15, 0.2

    Label:
        font_size: '40sp'
        id: hand_number
        text: app.winds[root.round_wind_index] + ' ' + str(root.dealership) + '-' + str(root.hand_redeals)

    BoxLayout:
        cols: 5
        orientation: 'horizontal'

        SmallRiichiStick:
            size_hint: 0.3, 0.8

        ScaleLabel:
            font_size: '30sp'
            text: str(root.riichi_sticks)
            halign: 'left'

        Label:
            text: ''

        HonbaStick:
            size_hint: 0.3, 0.8

        ScaleLabel:
            font_size: '30sp'
            text: str(root.honba_sticks)
            halign: 'left'
'''
