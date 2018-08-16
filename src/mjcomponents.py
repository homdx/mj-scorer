# -*- coding: utf-8 -*-

''' contains various visual components for the game '''

from kivy.app import App
from kivy.animation import Animation
from kivy.core.text import Label as CoreLabel
from kivy.properties import BooleanProperty, ListProperty, NumericProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from mjenums import Log, Result

class SelectableRecycleGridLayout(FocusBehavior, LayoutSelectionBehavior,
                                  RecycleGridLayout):
    ''' Adds selection & focus behaviours to RecycleGridLayout '''
    pass


class SelectableButton(RecycleDataViewBehavior, Button):
    ''' Add selection support to the Button '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(SelectableButton, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableButton, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)
        return False

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected

    def on_press(self):
        App.get_running_app().game.load_game_by_desc(self.text)


class ScaleLabel(Label):
    pass


class DeltaScoreOverlay(Widget):

    def __init__(self, **kwargs):
        super(DeltaScoreOverlay, self).__init__(**kwargs)
        App.get_running_app().delta_overlays.append(self.proxy_ref)


class MJTable(BoxLayout):
    cols = NumericProperty(0)
    col_headings = ListProperty([])

    def on_col_headings(self, *args):
        for idx in range(self.cols):
            # kivy reverses expected order of children
            self.ids.header.children[self.cols - 1 - idx].text = self.col_headings[idx]

    def on_cols(self, *args):
        for idx in range(self.cols):
            self.ids.header.add_widget(ScaleLabel())


class RiichiStick(Button):

    def __init__(self, **kwargs):
        super(RiichiStick, self).__init__(**kwargs)
        App.get_running_app().riichi_stick_refs.append(self.proxy_ref)

    def de_riichi(self, really_deriichi):
        app_root = App.get_running_app()
        if really_deriichi:
            app_root.log(
                Log.UNUSUAL,
                '%s confirmed de-riichi, %s' % (self.player.wind, self.player.player_name))
            app_root.log(
                Log.SCORE,
                '%sde-riichi, %s' % (self.player.wind, self.player.player_name))
            self.visible = 0
            self.player.score += 10
            app_root.game.riichi_sticks -= 1
            app_root.game.riichi_delta_this_hand[self.player.index] += 1
            app_root.set_headline('riichi cancelled')

        else:
            app_root.log(
                Log.INFO,
                '%s decided not to de-riichi, %s' % (self.player.wind, self.player.player_name))

    def pressed(self):
        app_root = App.get_running_app()

        if not app_root.game.in_progress or app_root.was_double_tap:
            return False

        if self.visible:
            app_root.log(
                Log.INFO,
                '%s asked to de-riichi, %s' % (self.player.wind, self.player.player_name))
            app_root.yesno_popup.angle = self.player.angle
            app_root.yesno_popup.callback = self.de_riichi
            app_root.yesno_popup.question = '[b]Are you sure you want to remove your riichi?[/b]'
            app_root.yesno_popup.true_text = "YES, remove the riichi"
            app_root.yesno_popup.false_text = "NO, keep the riichi"
            app_root.yesno_popup.open()
        else:
            app_root.log(Log.SCORE, '%s riichi, %s' % (self.player.wind, self.player.player_name))
            self.visible = 1
            self.player.score -= 10
            app_root.game.riichi_sticks += 1
            app_root.game.riichi_delta_this_hand[self.player.index] -= 1

        return True


class PlayerPosition(AnchorLayout):
    def __init__(self, **kwargs):
        super(PlayerPosition, self).__init__(**kwargs)
        App.get_running_app().players.append(self.proxy_ref)


class HandScreen(Screen):
    result = None

    def __get_score(self, msg, result):
        self.result = result
        app_root = App.get_running_app()
        app_root.set_headline(msg)
        app_root.log(Log.SCORE, msg)
        app_root.hanfubutton_callback = self.got_score
        app_root.screen_switch('hanfubuttons')

    def got_score(self, result):
        if isinstance(result, dict):
            self.result.update(result)
        else:
            self.result['score'] = result
        App.get_running_app().hand_end(self.result)

    def on_touch_up(self, touch):

        app_root = App.get_running_app()
        app_root.was_double_tap = touch.is_double_tap

        if not app_root.game.in_progress:
            return False

        for player in app_root.players:
            if player.children[0].collide_point(*touch.pos):
                break
        else:
            return False

        for first_player in app_root.players:
            if first_player.children[0].collide_point(*touch.opos):
                break
        else:
            return False

        if first_player == player:
            if touch.is_double_tap:
                riichi_bottom_left = player.children[0].to_parent(
                    player.ids.riichi.pos[0],
                    player.ids.riichi.pos[1])
                riichi_top_right = player.children[0].to_parent(
                    player.ids.riichi.pos[0] + player.ids.riichi.size[0],
                    player.ids.riichi.pos[1] + player.ids.riichi.size[1])

                xpos_ok = (riichi_bottom_left[0] <= touch.pos[0] <= riichi_top_right[0]
                           or
                           riichi_bottom_left[0] >= touch.pos[0] >= riichi_top_right[0])

                ypos_ok = (riichi_bottom_left[1] <= touch.pos[1] <= riichi_top_right[1]
                           or
                           riichi_bottom_left[1] >= touch.pos[1] >= riichi_top_right[1])

                if xpos_ok and ypos_ok:
                    # don't tsumo if the double click was on the riichi stick
                    return False

                self.__get_score('Tsumo by %s' % player.wind, {
                    'result': Result.TSUMO,
                    'winners': player.index})

            elif touch.time_end - touch.time_start > 2:
                app_root.log(Log.DEBUG, 'Long press recorded for %s' % player.wind)
                app_root.set_deltas(player.index, app_root.screen_back())
        else:
            self.__get_score(
                'RON by %s off %s' % (player.wind, first_player.wind),
                {'result': Result.RON,
                 'losers': first_player.index,
                 'winners': player.index})

        return True


class WindDisc(Widget):
    def __init__(self, **kwargs):
        super(WindDisc, self).__init__(**kwargs)
        App.get_running_app().wind_discs.append(self.proxy_ref)

    def animate(self):
        (Animation(visible=1)
         + Animation(progress=1-self.progress)
         + Animation(visible=0)
        ).start(self)


class Mjcomponents():

    @staticmethod
    def get_kv():
        CoreLabel.register(
            name='NanumGothic',
            fn_regular='NanumGothic-Regular.ttf',
            fn_bold='NanumGothic-Bold.ttf',
        )
        # (name, fn_regular, fn_italic=None, fn_bold=None, fn_bolditalic=None)
        return '''

#:import ScoreRow mjscoretable.ScoreRow

<ModalView>:
    background_color: 0, 0, 0, 1
    border: []
    auto_dismiss: False
    title: ''

<Label>:
    font_name: 'NanumGothic'
    color: 0.9, 0.9, 0.9, 1.0


<SelectableButton>:
    # Draw a background to indicate selection
    text_size: self.size
    halign: 'left'
    valign: 'middle'
    padding: 5, 5
    canvas.before:
        Color:
            rgba: (.0, 0.9, .1, .3) if self.selected else (0, 0, 0, 1)
        Rectangle:
            pos: self.pos
            size: self.size


<MJTable>:
    orientation: "vertical"
    data_items: []

    GridLayout:
        id: header
        size_hint: 1, None
        height: sp(25)
        cols: root.cols

    RecycleView:
        viewclass: 'SelectableButton'
        data: [{'text': str(x)} for x in root.data_items]
        SelectableRecycleGridLayout:
            spacing: 0, 10
            cols: root.cols
            default_size: None, dp(50)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'
            multiselect: False
            touch_multiselect: False


<DeltaScoreOverlay>:
    visible: 1
    angle: 0
    delta: 0
    size_hint: 0.2, 0.2

    canvas.before:
        PushMatrix
        Rotate:
            angle: root.angle
            origin: root.center
    canvas:
        Color:
            rgba: 0.1,0.1,0.4,root.visible * 0.9
        Rectangle:
            size: root.size
            pos: root.pos
    canvas.after:
        PopMatrix

    ScaleLabel:
        markup: True
        text: ScoreRow.format_data(root.delta, 'deltas', app.japanese_numbers)
        size: root.size
        pos: root.pos
        font_size: '40sp'


<DeltaScorePopup@ModalView>:
    auto_dismiss: False
    id: deltascores
    background_color: 0, 0, 0, 0
    FloatLayout:
        DeltaScoreOverlay:
            id: bottom
            pos_hint: {'x': 0.35, 'y': 0.2}
        DeltaScoreOverlay:
            id: right
            angle: 90
            pos_hint: {'x': 0.55, 'y': 0.45}
        DeltaScoreOverlay:
            id: top
            angle: 180
            pos_hint: {'x': 0.35, 'y': 0.7}
        DeltaScoreOverlay:
            id: left
            angle: 270
            pos_hint: {'x': 0.2, 'y': 0.45}


<YesNoPopup@Popup>:
    auto_dismiss: False
    angle: 0
    callback: None
    question: '?'
    true_text: 'Yes'
    false_text: 'No'

    title: ''
    auto_dismiss: False
    size_hint: 0.8, 0.8

    ScatterLayout:
        size_hint: 0.8, 0.8
        rotation: root.angle
        do_translation: False
        do_rotation: False
        do_scale: False

        BoxLayout:
            orientation: 'vertical'
            Label:
                halign: 'center'
                valign: 'center'
                #pos_hint: {'top': 1, 'left': 0.1}
                size_hint_y: 0.3
                text_size: self.parent.size
                markup: True
                text: root.question
            Button:
                halign: 'center'
                valign: 'center'
                #pos_hint: {'top': 0.64, 'left': 0.1}
                size_hint_y: 0.3
                text_size: self.parent.size
                markup: True
                text: root.true_text
                on_release: root.dismiss() or root.callback(True)
            Button:
                halign: 'center'
                valign: 'center'
                #pos_hint: {'top': 0.32}
                size_hint_y: 0.3
                text_size: self.parent.size
                markup: True
                text: root.false_text
                on_release: root.dismiss() or root.callback(False)


<PlayerPosition>:

    player_name: ' '
    score: 250
    wind: '?'
    angle: 0
    index: -1
    chombo_count: 0


    ScatterLayout:
        size_hint: 0.3, 0.2
        padding: 1
        rotation: root.angle
        do_translation: False
        do_rotation: False
        do_scale: False

        BoxLayout:
            padding: 0, 0, 0, 5
            orientation: 'vertical'

            RiichiStick:
                size_hint: 1,  0.6
                id: riichi
                player: root.proxy_ref

            ScaleLabel:
                valign: 'top'
                id: score
                markup: True
                font_size: '40sp'
                text: root.wind + ' [b]' + str(root.score) + '[sub][color=999999]00[/color][/sub][/b]'

            ScaleLabel:
                text: root.player_name
                font_size: '20sp'


<RiichiStick>:

    visible: 0
    player: None

    text: ''
    background_color: app.bg_colour
    background_down: ''
    background_normal: ''
    border: 0, 0, 0, 0
    on_release: self.pressed() # on_touch_down suppresses this - kivy bug

    canvas:
        Color:
            rgba: .5, .5, .5, 1 - self.visible
        Line:
            width: 1
            rounded_rectangle: self.x, self.y, self.width, self.height -2 , self.height / 2 - 1
        Line:
            width: 1
            circle: (self.center_x, self.center_y, self.height / 5)

        Color:
            rgba: .3, .3, 1., self.visible
        Line:
            width: self.height / 2 - 1
            points: [self.x + self.height / 2 + 1, self.y + self.height / 2, self.x + self.width - self.height / 2 - 1, self.y + self.height / 2]

        Color:
            rgba: 1., 1., 1., self.visible
        Ellipse:
            size: self.height/2, self.height/2
            pos: self.center_x - self.height/4, self.center_y - self.height/4


<ScaleLabel>:
    _scale: 1. if self.texture_size[0] < self.width else float(self.width) / self.texture_size[0]
    canvas.before:
        PushMatrix
        Scale:
            origin: self.center
            x: self._scale or 1.
            y: self._scale or 1.
    canvas.after:
        PopMatrix


<HanScreenButton@Button>:
    size_hint: 0.3, 0.15
    font_size: '20sp'
    background_color: .2, .2, .2, 1.
    text_size: self.width, None
    halign: 'center'


<Hanfubutton@HanScreenButton>:
    score: 0
    on_release: app.hanfubutton_pressed(self.score)


<WindDisc>:
    wind: '?'
    visible: 0
    start_x: 0.5
    delta_x: 0.4
    start_y: 0.1
    delta_y: 0.4
    start_angle: 0
    delta_angle: 90
    progress: 0

    pos_hint: {'center_x': root.start_x + root.delta_x * root.progress, 'center_y': root.start_y + root.delta_y * root.progress}
    size_hint: 0.18, 0.18
    canvas.before:
        PushMatrix
        Rotate:
            angle: root.start_angle + root.delta_angle * root.progress
            origin: root.center
    canvas.after:
        PopMatrix
    canvas:
        Color:
            rgba: 0.3,0.3,1.,root.visible
        Ellipse:
            size: root.size
            pos: root.pos
    ScaleLabel:
        text: root.wind
        color: 1.,1.,1.,root.visible
        pos: root.pos
        font_size: '40sp'
        halign: 'center'
        valign: 'center'
        size: root.size


<Mjmenu@ModalView>
    title: ''
    on_open: app.toggle_buttons()
    GridLayout:
        orientation: 'vertical'
        cols: 2
        rows: 5
        Button:
            text: 'Close Menu'
            on_release: root.dismiss()
        Button:
            text: 'Load game \\n from db'
            on_release: root.dismiss() or app.screen_switch('gameslist')
        Button:
            id: newgamebutton
            text: 'New game'
            disabled: True
            on_release: root.dismiss() or app.ask_names()
        Button:
            text: 'Finish game'
            on_release: root.dismiss() or app.ask_to_finish()
            id: finishgamebutton
            disabled: True
        Button:
            id: multipleronbutton
            text: 'Multiple rons'
            on_release: root.dismiss() or app.multiple_rons()
            disabled: True
        Button:
            id: chombobutton
            text: 'Chombo'
            disabled: True
            on_release: root.dismiss() or app.who_chomboed()
        Button:
            id: forgetlasthandbutton
            text: 'Forget last hand'
            disabled: True
            on_release: root.dismiss() or app.forget_last_hand()
        Button:
            text: 'Settings'
            on_release: root.dismiss() or app.open_settings()
        Button:
            text: 'Help'
            on_release: root.dismiss() or app.show_help()
        Button:
            text: 'Exit app'
            on_release: app.stop()

<Helptext@FloatLayout>:
    Label:
        pos_hint: {'left': 0.1, 'top': 1.0}
        font_size: '20sp'
        padding: 10, 10
        halign: 'left'
        valign: 'top'
        markup: True
        text_size: self.size
        text: "[b]Riichi:[/b]\\n Tap your riichi stick\\n\\n[b]Tsumo:[/b]\\n Double-tap your name or score. Nothing else needs a double-tap. Only tsumo.\\n\\n[b]Ron:[/b]\\n Swipe from loser to winner (so the swipe goes in the direction of payment)\\n\\n[b]Score differences:[/b]\\n long-press player"


<HelpPopup@Popup>:
    title: 'Help'
    auto_dismiss: False

    Helptext

        AnchorLayout:
            anchor_x: 'center'
            anchor_y: 'bottom'
            Button:
                size_hint: 1.0, 0.1
                font_size: '20sp'
                bold: True
                text: 'Close'
                on_release: root.dismiss()

'''