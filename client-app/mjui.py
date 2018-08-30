# -*- coding: utf-8 -*-
''' module containing the main user interface for the app '''
class Mjui(): # main UI
    ''' near-empty class which only exists to return the kv for the interface '''
    @staticmethod
    def get_kv():
        ''' return kv as utf8 string '''
        return '''

#:import FadeTransition kivy.uix.screenmanager.FadeTransition
#:import Ruleset mjenums.Ruleset

BoxLayout:
    orientation: 'vertical'
    canvas:
        Color:
            rgba: app.bg_colour
        Rectangle:
            size: self.size
            pos: self.pos

    BoxLayout:
        id: topbar
        orientation: 'horizontal'
        size: root.width, max(40, root.height/15)
        size_hint: None, None

        Button:
            on_release: app.do_menu()
            text: ''
            size_hint_x: 0.1
            pos_hint: {'x': 1}
            canvas:
                Color:
                    rgba: .9, .9, .9, 1
                Line:
                    width: 2
                    points: [self.x + self.width/4, self.y +     self.height / 4, self.x + self.width * 3/4, self.y +     self.height / 4]
                Line:
                    width: 2
                    points: [self.x + self.width/4, self.y + 2 * self.height / 4, self.x + self.width * 3/4, self.y + 2 * self.height / 4]
                Line:
                    width: 2
                    points: [self.x + self.width/4, self.y + 3 * self.height / 4, self.x + self.width * 3/4, self.y + 3 * self.height / 4]

        ScaleLabel:
            default_headline: 'ZAPS Mahjong Scorer'
            headline: self.default_headline
            id: headline
            markup: True
            text: self.headline
            font_size: '35sp'

    ScreenManager:
        transition: FadeTransition()
        id: manager

        Screen:
            name: 'welcome'

            Helptext

            AnchorLayout:
                anchor_y: 'bottom'
                Button:
                    size_hint: 1.0, 0.2
                    font_size: '40sp'
                    bold: True
                    text: "Start Game"
                    on_release: app.ask_names()


        Screen:
            name: 'scoresheet'
            FloatLayout
                MjScoreTable:
                    id: score_table
                    pos_hint: {'top': 1, 'left': 0}
                    size_hint: 1, 0.9
                Button:
                    text: 'Current\\nGame'
                    size_hint: 0.2, 0.1
                    pos_hint: {'bottom': 0, 'left': 0}
                    on_release: app.screen_back()
                Button:
                    text: 'New\\nGame'
                    id: new_game_button
                    size_hint: 0.2, 0.1
                    disabled: True
                    pos_hint: {'bottom': 0, 'right': 1}
                    on_release: app.ask_names()


        Screen:
            name: 'gameslist'
            on_enter: app.game.fill_games_table()
            FloatLayout:
                orientation: 'vertical'
                MJTable
                    pos_hint: {'top': 1, 'left': 0}
                    size_hint: 1, 0.9
                    id: games_table
                    cols: 1
                    data_items: ['']
                Button:
                    text: 'Back'
                    size_hint: 0.2, 0.1
                    pos_hint: {'bottom': 0, 'left': 0}
                    on_release: app.screen_back()


        HandScreen:
            id: handscreen
            name: 'hand'

            PlayerPosition:  # East
                id: p0
                wind: app.winds[0]
                anchor_x: 'center'
                anchor_y: 'bottom'

            PlayerPosition:  # South
                id: p1
                wind: app.winds[1]
                angle: 90
                anchor_x: 'right'
                anchor_y: 'center'

            PlayerPosition:  # West
                id: p2
                wind: app.winds[2]
                angle: 180
                anchor_x: 'center'
                anchor_y: 'top'

            PlayerPosition:  # North
                id: p3
                wind: app.winds[3]
                angle: 270
                anchor_x: 'left'
                anchor_y: 'center'

            AnchorLayout:
                anchor_x: 'right'
                anchor_y: 'top'
                padding: 1
                Button:
                    id: draw
                    text: 'Draw'
                    size_hint: 0.15, 0.1
                    on_release: app.itsadraw()

            AnchorLayout:
                anchor_x: 'left'
                anchor_y: 'bottom'
                padding: 1
                Button:
                    id: scoretablebutton
                    text: 'Scoresheet'
                    size_hint: 0.18, 0.1
                    font_size: '12sp'
                    on_release: app.screen_switch('scoresheet')

            AnchorLayout:
                anchor_x: 'center'
                anchor_y: 'center'
                MjGameStatus
                    id: game_status

            FloatLayout:

                WindDisc:
                    wind: app.winds[0]
                    start_x: 0.5
                    delta_x: 0.4
                    start_y: 0.1
                    delta_y: 0.4
                WindDisc:
                    wind: app.winds[1]
                    start_angle: 90
                    start_x: 0.9
                    delta_x: -0.4
                    start_y: 0.5
                    delta_y: 0.4
                WindDisc:
                    wind: app.winds[2]
                    start_angle: 180
                    start_x: 0.5
                    delta_x: -0.4
                    start_y: 0.9
                    delta_y: -0.4
                WindDisc:
                    wind: app.winds[3]
                    start_angle: 270
                    start_x: 0.1
                    delta_x: 0.4
                    start_y: 0.5
                    delta_y: -0.4



        Screen:
            name: 'hanfubuttons'
            id: hanfubuttons
            StackLayout:
                orientation: 'tb-lr'
                spacing: 5, 5
                Hanfubutton:
                    text: '1-30'
                    color: 1., 0.3, 0.3, 1.
                    score: 240
                Hanfubutton:
                    text: '2-30, 1-60'
                    color: 1., 0.3, 0.3, 1.
                    score: 480
                Hanfubutton:
                    text: '3-30, 2-60'
                    color: 1., 0.3, 0.3, 1.
                    score: 960
                Hanfubutton:
                    id: mangan_button
                    text: '4-30, 3-60'
                    color: 1., 0.3, 0.3, 1.
                    score: 1920
                Hanfubutton:
                    text: '1-40, 2-20'
                    color: 0.3, 1., 0.3, 1.
                    score: 320
                Hanfubutton:
                    text: '2-40, 3-20'
                    color: 0.3, 1., 0.3, 1.
                    score: 640
                Hanfubutton:
                    text: '3-40, 4-20'
                    color: 0.3, 1., 0.3, 1.
                    score: 1280
                Hanfubutton:
                    text: '2-25, 1-50'
                    color: 0.3, 0.3, 1., 1.
                    score: 400
                Hanfubutton:
                    text: '3-25, 2-50'
                    color: 0.3, 0.3, 1., 1.
                    score: 800
                Hanfubutton:
                    text: '4-25, 3-50'
                    color: 0.3, 0.3, 1., 1.
                    score: 1600
                HanScreenButton:
                    text: 'Other fu'
                    color: 0.3, 1., 1., 1.
                    on_release: app.screen_switch('hanfuother')
                HanScreenButton:
                    text: 'Cancel'
                    color: .5, 0.5, .5, 1.
                    on_release: app.cancel_end_of_hand()
                Hanfubutton:
                    text: 'Mangan'
                    color: 1., 1., 0.3, 1.
                    score: 2000
                Hanfubutton:
                    text: "Haneman\\n(6—7)"
                    color: 1., 1., 0.3, 1.
                    score: 3000
                Hanfubutton:
                    text: 'Baiman\\n(8—10)'
                    color: 1., 1., 0.3, 1.
                    score: 4000
                Hanfubutton:
                    text: 'Sanbaiman\\n(11—12)'
                    color: 1., 1., 0.3, 1.
                    score: 6000
                Hanfubutton:
                    text: 'Yakuman'
                    color: 1., 1., 0.3, 1.
                    score: 8000
                Hanfubutton:
                    text: 'Yakuman\\nwith Pao'
                    color: 1., 1., 0.3, 1.
                    score: 8888


        Screen:
            name: 'hanfuother'
            id: hanfuother
            StackLayout:
                orientation: 'tb-lr'
                spacing: 5, 5
                Hanfubutton:
                    text: '1-70'
                    color: 1., 0.3, 0.3, 1.
                    score: 560
                Hanfubutton:
                    text: '2-70'
                    color: 1., 0.3, 0.3, 1.
                    score: 1120
                Hanfubutton:
                    text: '1-80'
                    color: .3, 1, 0.3, 1.
                    score: 640
                Hanfubutton:
                    text: '2-80'
                    color: .3, 1, 0.3, 1.
                    score: 1280
                Hanfubutton:
                    text: '1-90'
                    color: .3, 1, 0.3, 1.
                    score: 720
                Hanfubutton:
                    text: '2-90'
                    color: .3, 1, 0.3, 1.
                    score: 1440
                Hanfubutton:
                    text: '1-100'
                    color: .3, .3, 1., 1.
                    score: 800
                Hanfubutton:
                    text: '2-100'
                    color: .3, .3, 1., 1.
                    score: 1600
                Hanfubutton:
                    text: '1-110'
                    color: .6, .3, .6, 1.
                    score: 880
                Hanfubutton:
                    text: '2-110'
                    color: .6, .3, .6, 1.
                    score: 1760
                HanScreenButton:
                    text: 'Other fu'
                    color: .5, 0.5, .5, 1.
                    on_release: app.screen_switch('hanfubuttons')
                HanScreenButton:
                    text: 'Cancel'
                    color: .5, 0.5, .5, 1.
                    on_release: app.cancel_end_of_hand()


        Screen:
            name: 'playernames'
            on_enter: player0name.focus = True
            BoxLayout:
                size_hint_y: 0.6
                pos_hint: {'top': 1}
                orientation: 'vertical'
                TextInput:
                    hint_text: 'Player 1 name'
                    id: player0name
                    write_tab: False
                    multiline: False
                    height: self.minimum_height
                    focus: True
                    on_text_validate: player1name.focus = True
                TextInput:
                    hint_text: 'Player 2 name'
                    height: self.minimum_height
                    write_tab: False
                    id: player1name
                    multiline: False
                    on_text_validate: player2name.focus = True
                TextInput:
                    hint_text: 'Player 3 name'
                    height: self.minimum_height
                    id: player2name
                    write_tab: False
                    multiline: False
                    on_text_validate: player3name.focus = True
                TextInput:
                    hint_text: 'Player 4 name'
                    height: self.minimum_height
                    id: player3name
                    write_tab: False
                    multiline: False
                BoxLayout:
                    orientation: 'horizontal'
                    Label:
                        text: 'Rules to use:'
                    ToggleButton:
                        group: 'ruleset'
                        text: 'EMA'
                        value: Ruleset.EMA2016
                        allow_no_selection: False
                        state: 'down'
                    ToggleButton:
                        group: 'ruleset'
                        text: 'WRC'
                        value: Ruleset.WRC2017
                        allow_no_selection: False
                Button:
                    id: allocatebutton
                    font_size: '20sp'
                    bold: True
                    text: 'Allocate seating and start game'
                    on_release: app.randomise_seating()

'''
