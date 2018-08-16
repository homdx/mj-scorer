# -*- coding: utf-8 -*-
'''

for who chombod, who ronned, who was tenpai at a draw

'''

from kivy.app import App
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.uix.popup import Popup
from kivy.uix.scatterlayout import ScatterLayout
from mjenums import Log, Result


class PlayerButton(ScatterLayout):
    root_popup = None


class Draw():

    __popup = None

    def __init__(self):
        self.__popup = Factory.Mjwhodidit()
        self.__popup.when_cancelled = self.cancelled
        self.__popup.when_done = self.when_done
        self.__popup.set_labels("Who is in tenpai?")
        self.__popup.group_playerbuttons(False) # allow multiple tenpai

    def cancelled(self):
        self.__popup.dismiss()

    def go(self):
        self.__popup.open()

    def when_done(self):
        out = {
            'losers': [],
            'result': Result.DRAW,
            'winners': self.__popup.get_selected_players()
            }
        self.__popup.dismiss()
        App.get_running_app().hand_end(out)


class Pao():

    __callback = None
    __popup = None
    __result = None

    def __init__(self):
        self.__popup = Factory.Mjwhodidit()
        self.__popup.when_cancelled = self.cancelled
        self.__popup.when_done = self.when_done
        self.__popup.when_ready = self.when_ready
        self.__popup.set_labels("Who is liable for the yakuman?")
        self.__popup.group_playerbuttons(True) # only one liable

    def cancelled(self):
        self.__popup.dismiss()

    def go(self, callback):
        self.__result = App.get_running_app().root.ids.handscreen.result
        self.__result['score'] = 8000
        self.__callback = callback
        self.__popup.open()

    def when_ready(self):
        self.__popup.min_players_selected = 1
        self.__popup.max_players_selected = 1
        self.__popup.player_buttons[self.__result['winners']].ids.button.disabled = True
        self.__popup.ids.whodiditdone.disabled = True

    def when_done(self):
        self.__result['liable'] = self.__popup.get_selected_players()[0]
        self.__popup.dismiss()
        self.__callback(self.__result)


class Chombo():

    __popup = None

    def __init__(self):
        self.__popup = Factory.Mjwhodidit()
        self.__popup.set_labels('Who chomboed?')
        self.__popup.group_playerbuttons(True) # only one chombo at a time
        self.__popup.when_cancelled = self.cancelled
        self.__popup.when_done = self.when_done
        self.__popup.when_ready = self.when_ready

    def cancelled(self):
        self.__popup.dismiss()

    def go(self):
        self.__popup.open()

    def when_ready(self):
        self.__popup.min_players_selected = 1
        self.__popup.max_players_selected = 1
        self.__popup.ids.whodiditdone.disabled = True

    def when_done(self):
        out = {
            'losers': self.__popup.get_selected_players()[0],
            'result': Result.CHOMBO,
            'winners': []
            }
        self.__popup.dismiss()
        App.get_running_app().hand_end(out)


class MultipleRons():

    __popup = None
    result = {}
    winners = []

    def __init__(self):
        self.__popup = Factory.Mjwhodidit()
        self.__popup.when_cancelled = self.cancelled

    def cancelled(self):
        self.__popup.dismiss()

    def go(self):
        app_root = App.get_running_app()
        app_root.log(Log.INFO, 'multiple ron')
        self.winners = []
        self.result = {
            'result': Result.MULTIPLE_RON,
            'winners': [],
            'losers': [],
            'score': [0, 0, 0, 0],
            }
        self.__popup.when_cancelled = self.cancelled
        self.__popup.when_ready = self.get_loser
        self.__popup.set_labels('Who dealt in?')
        self.__popup.when_done = self.got_loser
        self.__popup.open()

    def get_loser(self):
        self.__popup.group_playerbuttons(True) # only one loser
        self.__popup.ids.whodiditdone.disabled = True
        self.__popup.min_players_selected = 1
        self.__popup.max_players_selected = 1

    def got_loser(self):
        self.result['losers'] = self.__popup.get_selected_players()[0]
        self.__popup.dismiss()
        self.__popup.group_playerbuttons(False) # must have multiple winners
        self.__popup.set_labels("Who won?")
        self.__popup.when_ready = self.get_winners
        self.__popup.when_done = self.got_winners
        Clock.schedule_once(lambda dt: self.__popup.open(), 0.3)

    def get_winners(self):
        self.__popup.ids.whodiditdone.disabled = True
        self.__popup.min_players_selected = 2
        self.__popup.max_players_selected = 3
        self.__popup.player_buttons[self.result['losers']].ids.button.disabled = True

    def got_winners(self):
        selected = self.__popup.get_selected_players()
        self.__popup.dismiss()

        # the order we do these in, matters, because of riichi sticks,
        # so go clockwise from loser. We will be popping this array from the end,
        # so the array is in anti-clockwise order
        non_losers = list(range(self.result['losers'] + 1, 4)) + \
            list(range(0, self.result['losers']))

        self.winners = []
        for non_loser in non_losers:
            if non_loser in selected:
                self.winners.append(non_loser)

        self.result['winners'] = self.winners.copy()
        self.get_one_score()

    def get_one_score(self):
        app_root = App.get_running_app()
        app_root.root.ids.handscreen.result = {'winners': self.winners[-1]} # needed if we get pao
        app_root.set_headline(self.__get_headline())
        app_root.hanfubutton_callback = self.got_one_score
        app_root.screen_switch('hanfubuttons')

    def got_one_score(self, score):
        app_root = App.get_running_app()

        winner = self.winners[-1]
        if isinstance(score, dict):
            result = score.copy()
            result['losers'] = self.result['losers']
        else:
            result = {'winners': winner, 'score': score, 'losers': self.result['losers']}

        score_change = app_root.calculate_ron_scores(result)

        for idx in range(4):
            self.result['score'][idx] += score_change[idx]

        self.winners.pop() # done one winner, so remove it

        if self.winners:
            # there is at least one more winner to get the score of
            return app_root.deltascore_show(self.result['score'], self.get_one_score)

       # that was the last winner

        self.result['score'][winner] += 10 * app_root.game.riichi_sticks
        app_root.game.riichi_delta_this_hand[winner] += app_root.game.riichi_sticks
        app_root.game.riichi_sticks = 0

        return app_root.hand_end(self.result)

    def __get_headline(self):
        players = App.get_running_app().players
        winner = self.winners[-1]
        if len(self.winners) == len(self.result['winners']):
            # on first winner
            prefix = 'What'
        elif len(self.winners) == 1:
            # on last winner
            prefix = 'Finally, what'
        else:
            # on second winner of three
            prefix = 'And what'

        return '%s score did [b]%s[/b] get from %s' % (
            prefix,
            players[winner].wind,
            players[self.result['losers']].wind
            )

class Mjwhodidit(Popup):

    instances = []

    def __init__(self, *args, **kwargs):
        super(Mjwhodidit, self).__init__(*args, **kwargs)

        self.max_players_selected = 0
        self.min_players_selected = 0
        self.multiple_ron_winners = None
        self.when_ready = None
        self.when_done = None
        self.when_cancelled = None
        self.on_open = self.reset_playerbuttons

        self.player_buttons = self.check_children(self, PlayerButton)
        for button in self.player_buttons:
            button.root_popup = self

        Mjwhodidit.instances.append(self)

    @classmethod
    def check_children(cls, node, of_type):
        out = []
        for child in node.children:
            if isinstance(child, of_type):
                out.insert(0, child)
            out = cls.check_children(child, of_type) + out
        return out

    def get_selected_players(self):

        selected = []
        for index in range(4):
            if self.player_buttons[index].ids.button.state == 'down':
                selected.append(index)
                self.player_buttons[index].ids.button.state = 'normal'

        return selected

    def group_playerbuttons(self, to_group):
        for button in self.player_buttons:
            button.ids.button.group = 'a' if to_group else None

    def reset_playerbuttons(self):

        players = App.get_running_app().players
        for index in range(4):
            self.player_buttons[index].ids.button.state = 'normal'
            self.player_buttons[index].ids.button.disabled = False
            self.player_buttons[index].player_name = '%s\n%s' % (
                players[index].wind,
                players[index].player_name)
        if self.when_ready is not None:
            self.when_ready()

    def set_labels(self, text):
        for label in self.player_buttons:
            label.prompt = text

    def whodidit_check(self):
        '''
        a button on the whodidit screen has been pressed.
        Set the done button enabled state accordingly.
        '''
        if self.max_players_selected and self.min_players_selected:
            number_of_buttons_down = 0
            for idx in range(4):
                if self.player_buttons[idx].ids.button.state == 'down':
                    number_of_buttons_down += 1
            self.ids.whodiditdone.disabled = not(
                self.min_players_selected
                <= number_of_buttons_down
                <= self.max_players_selected)
        return False

    @staticmethod
    def get_kv():
        return '''

<PlayerButton>:
    player_name: ''
    prompt: ''
    root_popup: None

    do_translation: False
    do_rotation: False
    do_scale: False
    size_hint: 0.3, 0.3

    BoxLayout:
        orientation: 'vertical'
        ToggleButton:
            id: button
            size: root.size
            text_size : self.width, None
            halign: 'center'
            font_size: '20sp'
            on_state: root.root_popup.whodidit_check()
            text: root.player_name

        ScaleLabel:
            font_size: '24sp'
            text: root.prompt


<Mjwhodidit>:

    FloatLayout:
        Button:
            pos_hint: {'right': 1, 'bottom': 0}
            id: whodiditdone
            text: 'Done'
            bold: True
            size_hint: 0.15, 0.1
            on_release: root.when_done()

        Button:
            pos_hint: {'left': 0, 'bottom': 0}
            text: 'Cancel'
            size_hint: 0.15, 0.1
            on_release: root.when_cancelled()

        AnchorLayout:
            anchor_x: 'center'
            anchor_y: 'bottom'
            padding: 1

            PlayerButton:

        AnchorLayout:
            anchor_x: 'right'
            anchor_y: 'center'
            padding: 1

            PlayerButton:
                rotation: 90

        AnchorLayout:
            anchor_x: 'center'
            anchor_y: 'top'
            padding: 1

            PlayerButton:
                rotation: 180

        AnchorLayout:
            anchor_x: 'left'
            anchor_y: 'center'
            padding: 1

            PlayerButton:
                rotation: 270
'''
