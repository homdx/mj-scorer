# -*- coding: utf-8 -*-
'''
This module contains the functions for handling the start and end of hands and
games. and the UI for the status box in the centre of the screen during gameplay.

Ongoing games are saved after every scoring event in current_game.json. Only the
current loaded game is stored there.

Games are stored in the database when they are finished, and
when a different game is loaded, and when the app is closed.

'''

from datetime import datetime
import json
from pathlib import Path

from time import gmtime, strftime, time

from kivy.app import App
from kivy.properties import NumericProperty
from kivy.storage.jsonstore import JsonStore
from kivy.uix.boxlayout import BoxLayout

from mjcomponents import SelectableButton
from mjdb import Mjdb
from mjenums import Log, Rules


class MjGameStatus(BoxLayout):
    ''' class for game in progress, and completed games '''
    __db = Mjdb()
    __hand_count = 0
    __game_dict = {}
    __json_path = None
    __score_table = None
    __saved_game_attributes = ['game_id', 'start_time', 'in_progress']
    __start_of_hand_attributes = ['round_wind_index', 'dealership', 'hand_redeals']
    __end_of_hand_attributes = ['riichi_sticks', 'honba_sticks', ]

    dealership = NumericProperty(1)
    game_id = ''
    hand_redeals = NumericProperty(0)
    honba_sticks = NumericProperty(0)
    in_progress = False
    riichi_sticks = NumericProperty(0)
    riichi_delta_this_hand = [0, 0, 0, 0]
    round_wind_index = NumericProperty(0)
    rules = None
    start_time = NumericProperty(0)


    def check_before_resuming(self, ndx):
        if self.in_progress:
            self.save()
        self.load_game_by_index(ndx)


    def end_game(self):
        self.in_progress = False
        if not self.__hand_count:
            self.erase()
            return None

        app = App.get_running_app()
        self.__end_of_hand()

        scoretable = app.root.ids.score_table
        results = scoretable.ids
        scores = scoretable.update_scores()

        ordered_scores = sorted(scores, reverse=True)
        placement = [ordered_scores.index(app.players[idx].score) for idx in range(4)]
        all_uma = self.rules.uma[:]

        if self.rules.riichi_abandoned_at_end:
            adjustment_total = 0
        else:
            # award limbo riichi bets to first place if rules allow
            adjustment_total = 10 * self.riichi_sticks

        adjustments = [adjustment_total] + [0] * 3

        # calculation for sharing uma between tied places,
        # and sharing left-over riichi sticks between joint-first places

        # Note that there's a weird corner case:
        #   one riichi stick left over, and three players in joint first place.
        # 300 points each and just accept that the totals will be out by 0.1 (thousands)
        # Should really be 333 points: see this FB post by former EMA president Tina
        # https://www.facebook.com/groups/osamuko/permalink/1122431181120919/?comment_id=1123749627655741&comment_tracking=%7B%22tn%22%3A%22R0%22%7D

        if ordered_scores[0] == ordered_scores[1] == ordered_scores[2] == ordered_scores[3]:
            # 1111
            all_uma = [round(sum(all_uma)/4)] * 4
            adjustments = [int(adjustment_total/4)] * 4
        elif ordered_scores[1] == ordered_scores[2] == ordered_scores[3]:
            # 1222
            all_uma[1:] = [round(sum(all_uma[1:]) / 3)] * 3
        elif ordered_scores[0] == ordered_scores[1] == ordered_scores[2]:
            # 1114
            all_uma[0:3] = [round(sum(all_uma[0:3]) / 3)] * 3
            adjustments[0:3] = [int(adjustment_total/3)] * 3
        elif ordered_scores[0] == ordered_scores[1] and ordered_scores[2] == ordered_scores[3]:
            # 1133
            all_uma = [round(sum(all_uma[0:2]) / 2)] * 2 + [round(sum(all_uma[2:]) / 2)] * 2
            adjustments[0:2] = [int(adjustment_total/2)] * 2
        elif ordered_scores[1] == ordered_scores[2]:
            #1224
            all_uma[1:3] = [round(sum(all_uma[1:3]) / 2)] * 2
        elif ordered_scores[2] == ordered_scores[3]:
            #1233
            all_uma[2:] = [round(sum(all_uma[2:]) / 2)] * 2
        elif ordered_scores[0] == ordered_scores[1]:
            #1134
            all_uma[0:2] = [round(sum(all_uma[0:2]) / 2)] * 2
            adjustments[0:2] = [int(adjustment_total/2)] * 2
        #1234 - no changes needed

        for idx in range(4):

            net_score = scores[idx] - self.rules.starting_points
            results.net_scores.data_items[idx + 1] = net_score

            uma = all_uma[placement[idx]]
            results.scoretable_uma.data_items[idx + 1] = uma

            chombos = self.rules.chombo_value * app.players[idx].chombo_count
            results.scoretable_chombos.data_items[idx + 1] = chombos

            adjustment = adjustments[placement[idx]]
            results.scoretable_adjustments.data_items[idx + 1] = adjustment

            results.scoretable_final_totals.data_items[idx + 1] = \
                net_score + uma + chombos + adjustment

        self.save({
            'net_scores': results.net_scores.data_items[1:],
            'uma': results.scoretable_uma.data_items[1:],
            'chombos': results.scoretable_chombos.data_items[1:],
            'adjustments': results.scoretable_adjustments.data_items[1:],
            'final_score': results.scoretable_final_totals.data_items[1:]
        })

        scoretable.scroll_to(results.scoretable_final_totals)
        self.erase()


    def erase(self):
        self.__game_dict['current'] = {}
        self.sync()


    def fill_games_table(self, ongoing=None, add_new=False):
        ''' populate the games table with a list of games,
        and return the number of games listed
        '''
        self.__db.init()
        app = App.get_running_app()
        SelectableButton.callback = self.check_before_resuming
        app.games_list = self.__db.list_games(ongoing)

        # don't offer to restore older version of current game!
        for game in range(len(app.games_list)):
            if self.game_id == app.games_list[game][0]:
                del app.games_list[game]
                break

        if ongoing is not False and not self.in_progress:
            # get most recent game too, if not filtering on closed games only
            self.__json_path = str(Path(app.user_data_dir) / 'current_game.json')
            try:
                test = JsonStore(self.__json_path)
                if test['current']['in_progress']:
                    for game in range(len(app.games_list)):
                        if test['current']['game_id'] == app.games_list[game][0]:
                            del app.games_list[game]
                            break
                    app.games_list.insert(0,[
                        test['current']['game_id'],
                        test['description']['desc'],
                        test['current']])
            except:
                pass

        if add_new:
            app.games_list.insert(0, [None, 'New game', None])
        return len(app.games_list)


    def forget_last_hand(self, do_it):
        ''' restore game state to hand before last; remove last hand '''
        if not do_it:
            return True
        app = App.get_running_app()
        app.log(Log.UNUSUAL, 'Forget last hand')
        was_not_redeal = not self.hand_redeals
        if self.__restore_row(-2):
            app.set_headline('Last hand forgotton')
            if was_not_redeal:
                # rotate winds backwards only if the hand to be forgotten
                #   was NOT a dealer-continuation hand
                players = app.players
                lastwind = players[0].wind
                for player in range(3):
                    players[player].wind = players[player + 1].wind
                players[3].wind = lastwind
                app.animate_winddiscs('clockwise')

            self.__score_table.delete_row(-1)
            self.__game_dict['current']['hands'].pop()
            self.__hand_count = len(self.__game_dict['current']['hands']) - 1
            self.sync()
            self.__score_table.update_scores()
            app.popup_menu.ids['forgetlasthandbutton'].disabled = self.__hand_count == 1
        return True


    def game_summary(self):
        description = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' + (
            self.ids.hand_number.text if self.in_progress else '(ended)'
            ) + ': '

        app = App.get_running_app()
        for idx in range(4):
            description += '%s(%s), '% (
                self.__game_dict['current']['players'][idx]['name'],
                '%.1f' % ((
                    app.players[idx].score if self.in_progress else
                    self.__game_dict['current']['final_score'][idx]
                    ) / 10)
            )
        return description


    def get_summary(self):
        return self.__game_dict['description']['desc']


    def load_game_by_index(self, ndx):
        app = App.get_running_app()
        this_game = app.games_list[ndx]
        self.__reset()
        if this_game[0] is None:
            # new game
            app.ask_names()
            return

        self.__game_dict['current'] = \
            this_game[2] if type(this_game[2]) == dict else json.loads(this_game[2])

        self.resume()
        app.screen_switch('scoresheet')


    def log_append(self, log_type, log_text):
        timestamp = strftime("%Y-%m-%d %H:%M:%S Z", gmtime())

        if 'log' not in self.__game_dict['current']:
            self.__game_dict['current']['log'] = []
        self.__game_dict['current']['log'].append('%s\t%s\t%d\t%s\t%s' % (
            timestamp,
            self.ids.hand_number.text,
            log_type['priority'],
            log_type['text'],
            log_text
        ))


    def next_hand(self):
        self.__end_of_hand()
        self.__next_hand()


    def resume(self, do_resume=True):
        ''' if user has requested resumption,
        set the game state to the most recent one in the current game_dict
        '''
        app = App.get_running_app()

        if not do_resume:
            self.__reset()
            return False

        app.set_headline('Game restored')
        self.__score_table = app.root.ids.score_table

        if not self.__restore_row(-1):
            app.log(Log.ERROR, 'Failed to restore game')
            return False

        app.log(
            Log.DEBUG,
            'Restoring game on device ' + app.config.get('main', 'installation_id')
            )

        for item in self.__saved_game_attributes:
            setattr(self, item, self.__game_dict['current'][item])

        self.rules = Rules(self.__game_dict['current']['rules'])
        self.__rebuild_score_table()
        app.toggle_buttons()
        app.screen_switch('hand')

        windlist = app.winds + app.winds + app.winds
        for idx in range(4):
            app.players[idx].player_name = \
                app.root.ids['player%dname' % idx].text = \
                self.__game_dict['current']['players'][idx]['name']
            app.players[idx].index = idx
            app.players[idx].wind = windlist[5 + idx - self.dealership]

        app.popup_menu.ids['forgetlasthandbutton'].disabled = \
            not self.in_progress or self.__hand_count < 2

        return True


    def resumption_possible(self):
        ''' when starting up, check for ongoing games, and offer them,
        together with the option of starting a new game
        '''
        self.__db.init()
        return self.fill_games_table(ongoing=1, add_new=True)


    def save(self, results={}):
        ''' save the game to the games database'''
        if not 'players' in self.__game_dict['current']:
            return
        self.__game_dict['current'].update(results)
        self.__game_dict['current']['in_progress'] = self.in_progress
        description = self.game_summary()
        dict_to_save = self.__game_dict['current']
        self.__db.save_game(dict_to_save, description)
        dict_to_save['desc'] = description
        App.get_running_app().post_game(dict_to_save)


    def show_games(self, ongoing=True):
        '''user has asked for a list of games to choose from, so provide
        a scrollable list of selectable games.
        '''
        app = App.get_running_app()
        if self.in_progress:
            app.set_headline('Replace current game?')
        else:
            app.set_headline('Load game')
        self.fill_games_table(ongoing)
        app.screen_switch('gameslist')


    def start(self, ruleset=None, names=None):
        ''' initialise all variables for a new game '''

        app = App.get_running_app()

        self.__reset()
        self.rules = Rules(ruleset)
        for item in self.__saved_game_attributes:
            self.__game_dict['current'][item] = getattr(self, item)

        self.__game_dict['current']['players'] = []

        for idx in range(1,5):
            self.__game_dict['current']['players'].append(
                names[idx - 1] or {'id': -idx, 'name': 'player %d' % idx}
                )

        for idx in range(4):
            app.riichi_stick_refs[idx].visible = 0

        self.__game_dict['current']['rules'] = ruleset
        self.__game_dict['current']['start'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.__game_dict['current']['hands'] = [{'scores': [self.rules.starting_points] * 4}]
        self.next_hand()
        app.toggle_buttons()


    def sync(self):
        if not 'players' in self.__game_dict['current']:
            return
        self.__game_dict.put('description', desc=self.game_summary())


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
        for idx in range(4):
            self.__score_table.column_headings[idx + 1] = \
                self.__game_dict['current']['players'][idx]['name']
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
        app = App.get_running_app()

        self.__score_table = app.root.ids.score_table
        self.__score_table.reset()
        with open(self.__json_path, 'w') as f:
            f.write('')
        self.__game_dict = JsonStore(self.__json_path)
        self.__game_dict['current'] = {}

        self.__hand_count = 0
        self.dealership = 1
        self.start_time = time()
        self.game_id = app.config.get('main', 'installation_id') + str(int(self.start_time))
        self.game_log = []
        self.hand_redeals = 0
        self.honba_sticks = 0
        self.in_progress = True
        self.riichi_sticks = 0
        self.round_wind_index = 0


    def __restore_row(self, row=-2):
        app = App.get_running_app()
        try:
            last_row = self.__game_dict['current']['hands'][row]
            previous_row = self.__game_dict['current']['hands'][row - 1]

            for attr in self.__start_of_hand_attributes:
                setattr(self, attr, last_row[attr])

            for attr in self.__end_of_hand_attributes:
                setattr(self, attr, previous_row[attr])

            for idx in range(4):
                app.players[idx].score = previous_row['scores'][idx]

            self.__hand_count = len(self.__game_dict['current']['hands']) - 1
            self.riichi_delta_this_hand = 4 * [0]

            return True

        except Exception as err:
            app.log(
                Log.ERROR,
                "Failed to restore hand %d: %s" % (row, str(err))
                )
            app.set_headline('Failed to delete last hand')
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
