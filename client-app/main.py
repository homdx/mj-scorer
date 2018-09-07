# -*- coding: utf-8 -*-
"""
ZAPS Mahjong Scorer, on Android; Kivy + Python
@author: ZAPS

This is the main app file. All other client stuff is loaded from here.
"""

# the following line is used by the builder. Don't mess with the spacing!
__version__ = '0.2.4'


from kivy.config import Config # pylint: disable=wrong-import-order,ungrouped-imports
# These config settings MUST be done before any other modules are loaded
Config.set('postproc', 'double_tap_distance', '100') # pylint: disable=wrong-import-position
Config.set('postproc', 'double_tap_time', '650') # pylint: disable=wrong-import-position

import cProfile
from functools import partial
from hashlib import md5
from math import ceil, fabs, copysign
from pathlib import Path
import random # for randomising seat placement
from time import gmtime, strftime, time

# kivy libraries

import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, StringProperty
from kivy.uix.behaviors.togglebutton import ToggleButtonBehavior
from kivy.uix.settings import SettingsWithTabbedPanel

# components supplied with this app

from mjcomponents import Mjcomponents, SettingButton, SettingPassword
from mjenums import Log, Result
from mjgame import MjGameStatus
from mjplayers import PlayerNames
from mjscoretable import MjScoreTable
from mjsettings import settings_json
from mjwhodidit import Chombo, Draw, Mjwhodidit, MultipleRons, Pao
from mjui import Mjui
from salt import HASH_SALT

kivy.require("1.10.0")


class MahjongScorer(App):
    '''
    Main scoring class, storing game status

    '''

    __callback_ref = None
    __chombo = None
    __draw = None
    __log_to_server = Log.SCORE
    __multiplerons = None
    __pao = None
    __popup_help = None
    __profile = None

    auth_token = None
    bg_colour = ListProperty([0, 0, 0, 1])
    delta_overlays = ListProperty([])
    deltascore_popup = None
    deriichi_popup = None
    game = None
    games_list = ListProperty([])
    hanfubutton_callback = None
    japanese_numbers = BooleanProperty(False)
    players = ListProperty([])
    popup_menu = None
    riichi_stick_refs = ListProperty([])
    screen_stack = []
    was_double_tap = False
    wind_discs = ListProperty([])
    winds = StringProperty('東南西北')
    yesno_popup = None


    def add_score_line(self, score_deltas, line_description=None, new_section=False):
        if line_description is None:
            line_description = self.game.ids.hand_number.text
        data_row = score_deltas[:]
        data_row.insert(0, line_description)
        self.game.update_score(data_row, new_section)


    def animate_winddiscs(self, direction='anti-clockwise'):
        for disc in range(4):
            self.wind_discs[disc].progress = 0 if direction == 'anti-clockwise' else 1
            self.wind_discs[disc].wind = self.players[disc].wind
            self.wind_discs[disc].animate()


    def ask_names(self):
        self.set_headline("Please enter players' names")
        self.screen_switch('playernames')


    def ask_to_finish(self):
        self.yesno_popup.angle = 0
        self.yesno_popup.callback = self.game_end
        self.yesno_popup.question = "[b]Really finish the game? This can't be undone[/b]"
        self.yesno_popup.true_text = 'YES, finish game'
        self.yesno_popup.false_text = 'NO, continue the game'
        self.yesno_popup.open()


    def ask_to_resume(self, *args):
        nGames = self.game.resumption_possible()
        self.screen_switch('gameslist' if nGames > 1 else 'playernames')
        for each_widget in ['ongoinggamesbutton', 'completedgamesbutton']:
            self.popup_menu.ids[each_widget].disabled = False


    def build(self):
        Config.set('kivy', 'exit_on_escape', '0')

        self.title = 'ZAPS Mahjong Scorer'
        self.settings_cls = SettingsWithTabbedPanel
        self.use_kivy_settings = False

        Builder.load_string(Mjcomponents.get_kv())
        Builder.load_string(MjGameStatus.get_kv())
        Builder.load_string(MjScoreTable.get_kv())
        Builder.load_string(Mjwhodidit.get_kv())
        Builder.load_string(PlayerNames.get_kv())

        root = Builder.load_string(Mjui.get_kv())

        self.game = root.ids['game_status']
        self.yesno_popup = Factory.YesNoPopup()
        self.deltascore_popup = Factory.DeltaScorePopup()
        self.popup_menu = Factory.Mjmenu()

        Window.release_all_keyboards()
        Window.bind(on_keyboard=self.key_input)

        self.japanese_numbers = self.config.getboolean('main', 'japanese_numbers')
        self.set_wind_labels(self.config.getboolean('main', 'japanese_winds'))
        self.auth_token = self.config.get('main', 'auth_token')

        self.bg_colour = self.__get_gb_color(self.config.get('main', 'bg_colour'))
        return root


    def build_config(self, config):
        config.setdefaults('main', {
            'installation_id': str(time()).replace('.', '').replace(',', '')[-10:],
            'use_server': False,
            'bg_colour': 'black',
            'japanese_numbers': False,
            'japanese_winds': True,
            'auth_token': '',
            'auth_browser': '',
        })
        config.setdefaults('unused', {
            'api_path': 'https://mj.bacchant.es/api/v0/',
            'profiling': False,
            'api_store': '',
            'api_password': '',
            'auth_token': '',
        })


    def build_settings(self, settings):
        settings.register_type('password', SettingPassword)
        settings.register_type('button', SettingButton)
        settings.add_json_panel('', self.config, data=settings_json)


    def calculate_ron_scores(self, result):
        winner = result['winners']
        east_is_winner = self.players[winner].wind == self.winds[0]
        score_change = 4 * [0]
        delta = self.mj_round((6 if east_is_winner else 4) * result['score'])
        honba_bonus = 3 * self.game.honba_sticks
        score_change[result['winners']] = delta + honba_bonus
        try:
            pao = result['liable']
            score_change[result['losers']] = -delta // 2 - honba_bonus
            # using += just in case loser = liable anyway
            score_change[pao] += -delta // 2
        except:
            score_change[result['losers']] = -delta - honba_bonus

        self.log(
            Log.SCORE,
            'Ron of hand value %d by %s off %s' % (
                result['score'], winner, result['losers']))

        self.__de_riichi(winner)

        return score_change


    def cancel_end_of_hand(self):
        self.log(Log.UNUSUAL, 'cancelling end of hand')
        self.screen_switch('hand')
        self.set_headline('End of Hand has been cancelled')


    def close_settings(self, *args):
        self.screen_back()
        super(MahjongScorer, self).close_settings(*args)


    def deltascore_show(self, score_change, callback=None):
        for idx in range(4):
            self.delta_overlays[idx].delta = score_change[idx]
        self.__deltascore_show(callback)


    def do_menu(self):
        self.popup_menu.open()


    def forget_last_hand(self):
        # check that users really want this, before doing it
        self.yesno_popup.angle = 0
        self.yesno_popup.callback = self.game.forget_last_hand
        self.yesno_popup.question = '[b]Really forget the last hand?[/b]'
        self.yesno_popup.true_text = "YES, forget it"
        self.yesno_popup.false_text = "NO"
        self.yesno_popup.open()


    def game_end(self, really_end=True):
        if not really_end:
            return
        self.set_headline('Game over')
        self.popup_menu.ids['forgetlasthandbutton'].disabled = True
        if self.game.end_of_game() is None:
            self.toggle_buttons()
            return

        scoretable = self.root.ids.score_table
        results = scoretable.ids
        scores = scoretable.update_scores()

        ordered_scores = sorted(scores, reverse=True)
        placement = [ordered_scores.index(self.players[idx].score) for idx in range(4)]
        all_uma = self.game.rules.uma[:]

        if self.game.rules.riichi_abandoned_at_end:
            adjustment_total = 0
        else:
            # award limbo riichi bets to first place if rules allow
            adjustment_total = 10 * self.game.riichi_sticks

        adjustments = [adjustment_total] + [0] * 3

        # calculation for sharing uma between tied places,
        # and sharing left-over riichi sticks between joint-first places

        # Note that there's a weird corner case.
        # one riichi stick left over, and three players in joint first place?
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

            net_score = scores[idx] - self.game.rules.starting_points
            results.net_scores.data_items[idx + 1] = net_score

            uma = all_uma[placement[idx]]
            results.scoretable_uma.data_items[idx + 1] = uma

            chombos = self.game.rules.chombo_value * self.players[idx].chombo_count
            results.scoretable_chombos.data_items[idx + 1] = chombos

            adjustment = adjustments[placement[idx]]
            results.scoretable_adjustments.data_items[idx + 1] = adjustment

            results.scoretable_final_totals.data_items[idx + 1] = \
                net_score + uma + chombos + adjustment

        self.game.save({
            'net_scores': results.net_scores.data_items[1:],
            'uma': results.scoretable_uma.data_items[1:],
            'chombos': results.scoretable_chombos.data_items[1:],
            'adjustments': results.scoretable_adjustments.data_items[1:],
            'final_score': results.scoretable_final_totals.data_items[1:]
        })

        self.screen_switch('scoresheet')
        self.toggle_buttons()
        scoretable.scroll_to(results.scoretable_final_totals)
        self.game.erase()


    def game_end_userchoice(self, was_draw, game_end):
        if game_end:
            self.game_end()
        else:
            self.next_dealership(was_draw)


    def game_start(self, names):

        self.popup_menu.ids['forgetlasthandbutton'].disabled = True
        game_ruleset = None
        for button in ToggleButtonBehavior.get_widgets('ruleset'):
            if button.state == 'down':
                game_ruleset = button.value
                break

        self.game.start(ruleset=game_ruleset, names=names)
        self.screen_stack = []
        self.root.ids.score_table.reset()

        for idx in range(4):
            self.players[idx].wind = self.winds[idx]
            self.players[idx].score = self.game.rules.starting_points
            self.players[idx].chombo_count = 0

        self.set_headline('Game on!')
        self.screen_switch('hand')


    def hand_end(self, result):
        '''
        process the score, and allocate points to players
        '''

        if result['result'] == Result.CHOMBO:
            chomboed = result['losers']
            self.players[chomboed].chombo_count += 1
            deltas = [''] * 4
            deltas[chomboed] = '⊗'
            self.add_score_line(score_deltas=deltas, line_description='Chombo')
            self.screen_back()
            return

        self.set_headline()

        if isinstance(result['winners'], int):
            winning_winds = [self.players[result['winners']].wind]
        else:
            winning_winds = [self.players[winner].wind for winner in result['winners']]

        east_is_winner = self.winds[0] in winning_winds
        was_draw = result['result'] == Result.DRAW

        if was_draw:
            score_change = self.__calculate_draw_scores(result['winners'])
        elif result['result'] == Result.TSUMO:
            score_change = self.__calculate_tsumo_scores(east_is_winner, result)
        elif result['result'] == Result.RON:
            score_change = self.calculate_ron_scores(result)
            score_change[result['winners']] += 10 * self.game.riichi_sticks
            self.game.riichi_sticks = 0
        elif result['result'] == Result.MULTIPLE_RON:
            score_change = result['score']
        else:
            self.log(Log.ERROR, 'Unknown result type: '+ str(result))
            self.screen_switch('hand')
            return

        for player in range(4):
            self.players[player].score += score_change[player]

        self.deltascore_show(score_change)

        for idx in range(4):
            if self.riichi_stick_refs[idx].visible:
                score_change[idx] -= 10

        self.add_score_line(
            score_change,
            new_section=self.game.dealership == 1 and self.game.hand_redeals == 0)
        self.log(Log.SCORE, score_change)

        self.screen_switch('hand')
        self.popup_menu.ids['forgetlasthandbutton'].disabled = False
        self.next_hand(east_is_winner, was_draw)


    def hanfubutton_pressed(self, *args):
        '''
        Handle the pressing of a score button.
        Use a callback here, as we take a different route, depending on whether
        this is multiple ron or not
        '''
        if args[0] == 8888:
            if self.__pao is None:
                self.__pao = Pao()
            self.__pao.go(self.hanfubutton_callback)
        else:
            self.hanfubutton_callback(*args)


    def is_this_game_end(self, was_draw):
        self.yesno_popup.angle = 0
        self.yesno_popup.callback = partial(self.game_end_userchoice, was_draw)
        self.yesno_popup.question = \
            '[b]End of the %s round. End the game now? (This cannot be undone!)[/b]' \
            % self.winds[self.game.round_wind_index]
        self.yesno_popup.true_text = "YES"
        self.yesno_popup.false_text = "NO, play the next round"
        self.yesno_popup.open()


    def itsadraw(self):
        if self.game.in_progress:
            if self.__draw is None:
                self.__draw = Draw()
            self.__draw.go()
            return True
        return False


    @staticmethod
    def key_input(window, key, scancode, codepoint, modifier):
        if key == 27:
            return True  # override the default behaviour; the key now does nothing
        return False


    def log(self, log_type, action):
        '''
        store audit trail of all relevant events, and eventually store on server too
        '''
        timestamp = strftime("%Y-%m-%d %H:%M:%S Z", gmtime())
        print(timestamp + ' ' + str(action))
        self.game.game_log.append(timestamp + ' ' + str(action))


    @staticmethod
    def mj_round(score):
        '''
        round scores up to the nearest hundred, which we store as integers
        '''
        return int(copysign(ceil(fabs(score)/100), score))


    def multiple_rons(self):
        if self.__multiplerons is None:
            self.__multiplerons = MultipleRons()
        self.__multiplerons.go()


    def next_hand(self, east_is_winner, was_draw):
        for stick in self.riichi_stick_refs:
            stick.visible = 0

        if east_is_winner:
            self.game.honba_sticks += 1
            self.game.hand_redeals += 1
            self.game.next_hand()
        elif self.game.dealership == 4 and self.game.round_wind_index:
            if self.game.round_wind_index < 3:
                self.is_this_game_end(was_draw)
            else:
                # had all four wind rounds, so force end of game
                self.game_end()
        else:
            self.next_dealership(was_draw)


    def next_dealership(self, was_draw):
        self.game.honba_sticks = self.game.honba_sticks + 1 if was_draw else 0
        self.game.hand_redeals = 0
        self.game.dealership += 1
        if self.game.dealership > 4:
            self.game.dealership = 1
            self.game.round_wind_index += 1

        self.animate_winddiscs()
        lastwind = self.players[3].wind
        for player in range(3, 0, -1):
            self.players[player].wind = self.players[player - 1].wind
        self.players[0].wind = lastwind

        self.game.next_hand()


    def on_config_change(self, config, section, key, value):
        if config is not self.config or section != 'main':
            return

        if key == 'bg_colour':
            self.bg_colour = self.__get_gb_color(value)

        elif key == 'japanese_numbers':
            # need to do this silly dance because value is a string,
            # and because bool('0') is True in Python
            self.japanese_numbers = bool(int(value))

        elif key == 'japanese_winds':
            self.set_wind_labels(bool(int(value)))

        elif key == 'profiling':
            profiling = bool(int(value))
            Config.set('kivy', key, profiling)
            if profiling:
                self.__profile = cProfile.Profile()
                self.__profile.enable()
            else:
                self.__end_profiling()

        elif key == 'auth_token':
            self.auth_token = md5(bytes(value, 'utf-8') + HASH_SALT).hexdigest()


    def on_pause(self):
        ''' mobile OS has paused the app '''
        # TODO take this opportunity to try to sync all outstanding updates with the server
        return True


    def on_resume(self):
        ''' mobile OS has resumed the app '''
        pass


    def on_start(self):
        if self.config.getboolean('main', 'profiling'):
            self.__profile = cProfile.Profile()
            self.__profile.enable()


    def on_stop(self):
        ''' end app, so end profiler and dump its stats for later analysis '''
        # https://docs.python.org/3.6/library/profile.html
        if self.game.in_progress:
            self.game.sync()
            self.game.save()
        self.__end_profiling()
        Window.close()


    def randomise_seating(self, randomise):
        '''
        Received user names, so randomise the seating order, and start the game
        '''
        names = []

        seating_order = random.sample(range(4), 4) if randomise else (0, 1, 2, 3)
        for player in range(4):
            self.players[player].index = player
            next_name = self.root.ids['player%dname' % seating_order[player]].text
            self.players[player].player_name = next_name
            names.append(next_name)
            # first column of score table is hand name, so player columns are shifted right by 1
            self.root.ids.score_table.column_headings[player + 1] = next_name

        self.game_start(names)


    def register_new_player(self):
        ''' send a new player's details to the server '''
        self.log(Log.ERROR, '#TODO: MahjongScorer.register_new_player not yet coded')


    def screen_back(self):
        current_screen = self.root.ids.manager.current
        next_screen = current_screen
        while self.screen_stack and next_screen == current_screen:
            next_screen = self.screen_stack.pop()
        self.root.ids.manager.current = next_screen


    def screen_switch(self, where_to):
        ''' switch screen, and remember where we came from, so we can go back to it'''
        current_screen = self.root.ids.manager.current
        if where_to == 'hand':
            self.screen_stack = []
        else:
            self.screen_stack.append(current_screen)
        self.root.ids.manager.current = where_to


    def set_deltas(self, player_index, callback):
        for i in range(4):
            if i == player_index:
                delta = self.players[i].score
            else:
                delta = self.players[i].score - self.players[player_index].score
            self.delta_overlays[i].delta = delta
        self.__deltascore_show(callback)


    def set_headline(self, text=''):
        self.root.ids.headline.headline = text


    def set_wind_labels(self, japanese_winds):
        self.winds = '東南西北' if japanese_winds else 'ESWN'


    def show_help(self):
        if self.__popup_help is None:
            self.__popup_help = Factory.HelpPopup()
        self.__popup_help.open()


    def toggle_buttons(self):
        self.root.ids.new_game_button.disabled = self.game.in_progress
        if self.popup_menu is None:
            return

        for each_widget in ['chombobutton', 'finishgamebutton']:
            self.popup_menu.ids[each_widget].disabled = not self.game.in_progress

        for each_widget in ['newgamebutton',]:
            self.popup_menu.ids[each_widget].disabled = self.game.in_progress

        self.popup_menu.ids.multipleronbutton.disabled = \
            not self.game.in_progress \
            or self.game.rules is None \
            or not self.game.rules.multiple_rons


    def who_chomboed(self):
        if self.__chombo is None:
            self.__chombo = Chombo()
        self.__chombo.go()

# ============================================================================


    def __calculate_draw_scores(self, winners):
        score_change = 4 * [0]
        tenpai_count = len(winners)
        if 0 < tenpai_count < 4:
            noten = self.mj_round(-3000 / (4 - tenpai_count))
            tenpai = self.mj_round(3000 / tenpai_count)
            for player in range(0, 4):
                score_change[player] = tenpai if player in winners else noten
        return score_change


    def __calculate_tsumo_scores(self, east_is_winner, result):
        score = result['score']
        self.log(
            Log.SCORE,
            'Tsumo of hand value %d for %s' % (score, result['winners']))
        delta1 = self.mj_round(score + 100 * self.game.honba_sticks)
        delta2 = self.mj_round(2 * score + 100 * self.game.honba_sticks)
        if east_is_winner:
            try:
                pao = result['liable']
                score_change = 4 * [0]
                score_change[pao] = -3 * delta2
            except:
                score_change = 4 * [-delta2]
            score_change[result['winners']] = 3 * delta2
        else:
            try:
                pao = result['liable']
                score_change = 4 * [0]
                score_change[pao] = -2 * delta1 - delta2
            except:
                score_change = 4 * [-delta1]
                for index in range(4):
                    if self.players[index].wind == self.winds[0]:
                        score_change[index] = -delta2
                        break
            score_change[result['winners']] = 2 * delta1 + delta2

        self.__de_riichi(result['winners'])

        score_change[result['winners']] += 10 * self.game.riichi_sticks
        self.game.riichi_sticks = 0
        return score_change


    def __de_riichi(self, winner):
        if self.riichi_stick_refs[winner].visible:
            self.riichi_stick_refs[winner].visible = 0
            self.players[winner].score += 10
            self.game.riichi_sticks -= 1


    def __deltascore_show(self, callback=None):
        self.deltascore_popup.open()
        self.__callback_ref = Clock.schedule_once(
            lambda dt: (callback and callback()) or self.deltascore_popup.dismiss(),
            3)


    def __end_profiling(self):
        try: # because profiling may be off
            self.__profile.disable()
            self.__profile.dump_stats(str(Path(self.user_data_dir) / 'myapp.profile'))
        except:
            pass


    @staticmethod
    def __get_gb_color(value):
        return {'black': (0, 0, 0, 1),
                'dark blue': (0, 0, 0.1, 1),
                'dark green': (0, 0.1, 0, 1),
                'dark grey': (0.05, 0.05, 0.05, 1),
                'dark red': (0.15, 0, 0, 1)}[value]


if __name__ == "__main__":
    MahjongScorer().run()
