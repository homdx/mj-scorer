# -*- coding: utf-8 -*-
'''
Get player names, authentication and authorisation
'''

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput

from mjcomponents import SelectableButton


class AutoComplete_TextInput(TextInput):
    '''
    auto-complete text box which offers suggestions based on
    substrings of entered text
    '''
    base_list = []
    word_list = ListProperty([])
    prepared_word_list = []
    min_length_to_match = 1


    def fill_users_table(self, users):
        self.base_list = users
        self.word_list = self.base_list
        self.prepared_word_list = []
        for word in self.base_list:
            self.prepared_word_list.append(self.prepare_string(word[1]))


    def on_text(self, instance, value):
        # find all the occurrence of the substring
        test = self.prepare_string(value)
        try:
            this_index = self.prepared_word_list.index(test)
        except ValueError:
            this_index = None
            if self.min_length_to_match > len(test):
                self.word_list = self.base_list
                return

        self.word_list = []
        perfect_match_index = None
        for i in range(len(self.prepared_word_list)):
            # TODO this will get very slow when there's a lot of users
            if test in self.prepared_word_list[i]:
                if i == this_index:
                    perfect_match_index = len(self.word_list)
                self.word_list.append(self.base_list[i])

        if perfect_match_index is not None:
            Clock.schedule_once(
                lambda dt: self.table.scroll_to_index(perfect_match_index)
            )


    @staticmethod
    def prepare_string(value):
        return value.replace(' ', '').replace('.', '').replace(',', '').lower()


class MJauto(BoxLayout):

    __current_player = 0

    def get_player(self, player_number):
        app = App.get_running_app()
        SelectableButton.callback = self.got_registered_player
        self.__current_player = player_number
        app.set_headline("Select Player %d" % self.__current_player)
        self.ids.txt_input.focus = True
        self.ids.casualbutton.disabled = False


    def got_registered_player(self, result):
        player = self.ids.users_table.data_items[result]
        self.next_player(*player)


    def new_player(self, register=False):
        self.ids.casualbutton.disabled = True
        name = self.ids.txt_input.text
        if register:
            pass # TODO create new registered user
        else:
            self.next_player(-self.__current_player, name)


    def next_player(self, user_id, name):

        app = App.get_running_app()

        this_player_label = app.root.ids[
            'player%dname' % (self.__current_player - 1)]

        this_player_label.text = name
        this_player_label.user_id = user_id
        self.ids.txt_input.text = ''

        if self.__current_player < 4:
            app.set_headline(name)
            Clock.schedule_once(lambda dt: self.get_player(self.__current_player + 1), 1)
        else:
            app.set_headline("Hey! Oh! Let's go!")
            app.screen_switch('choose_rules')


class PinButton(Button):

    def on_release(self):
        self.parent.parent.press(self.text)


class PinDigit(Label):
    pass


class PinPad(BoxLayout):
    pin = StringProperty('')
    digits = None


    def ensure_digits(self):
        if self.digits is None:
            self.digits = []
            for child in self.children[1].children:
                self.digits.insert(0, child)


    def press(self, keypress):
        self.ensure_digits()
        if keypress == 'Cancel':
            self.reset()
            self.parent.got_pin(None)

        for ndx in range(4):
            if not self.digits[ndx].in_focus:
                continue
            if keypress == '⇦':
                if ndx:
                    self.digits[ndx].in_focus = False
                    self.digits[ndx - 1].in_focus = True
                    self.digits[ndx].done = False
                    self.digits[ndx - 1].done = False
                    self.pin = self.pin[0 : ndx - 1]
            else:
                self.digits[ndx].in_focus = False
                self.digits[ndx].done = True
                self.pin += keypress
                if ndx == 3:
                    self.parent.got_pin(self.pin)
                else:
                    self.digits[ndx + 1].in_focus = True
            break


    def reset(self):
        self.ensure_digits()
        self.pin = ''
        for ndx in range(4):
            self.digits[ndx].in_focus = False
            self.digits[ndx].done = False
        self.digits[0].in_focus = True


class PinPadPopup(Popup):

    callback = None

    def got_pin(self, pin):
        self.dismiss()
        self.callback(pin)


class PlayerUI():

    @staticmethod
    def get_kv():
        return '''

<PlayerTypeButton@Button>:
    padding: 5,5
    valign: 'center'
    halign: 'center'
    size_hint_x: None
    text_size: None, self.height
    width: self.texture_size[0]


<PlayerType@BoxLayout>:
    orientation: 'horizontal'
    spacing: 10
    TextInput:
        hint_text: 'Player (user)name'
        write_tab: False
        multiline: False
        height: self.minimum_height
        focus: True

    PlayerTypeButton:
        text: 'Find'


<MJauto>:
    orientation: 'vertical'
    spacing: 0, 2
    padding: 0

    AutoComplete_TextInput:
        hint_text: 'Enter username, then tap it in the list below'
        focus: True
        readonly: False
        multiline: False
        id: txt_input
        table: users_table
        size_hint_y: 0.15
        height: self.minimum_height

    GridLayout:
        cols: 2
        size_hint_y: 0.2
        Button:
            id: registerbutton
            text: 'Register\\nnew player'
            on_release: root.new_player(register=True)
            disabled: True
        Button:
            id: casualbutton
            text: "Casual player -\\nDon't register"
            on_release: root.new_player(register=False)

    MJTable:
        id: users_table
        txt_input: txt_input
        cols: 1
        data_items: txt_input.word_list


<LoginPopup@Popup>:

    title: 'Register this device to store your games on server'
    auto_dismiss: False
    on_open: username.focus = True

    BoxLayout:
        size_hint: 0.9, 0.6
        pos_hint: {'top': 1}
        orientation: 'vertical'

        TextInput:
            hint_text: "User name as registered"
            id: username
            write_tab: False
            multiline: False
            height: self.minimum_height
            focus: True
            size_hint_y: 0.18
            on_text_validate: password.focus = True
        TextInput:
            size_hint_y: 0.18
            hint_text: "Website password"
            id: password
            write_tab: False
            multiline: False
            height: self.minimum_height
            password: True
        Button:
            size_hint_y: 0.25
            id: loginbutton
            font_size: '15sp'
            bold: True
            text: 'Login'
            on_release: app.register_device(root, username.text, password.text)
        Button:
            size_hint_y: 0.25
            id: cancelbutton
            font_size: '15sp'
            bold: True
            text: 'Cancel'
            on_release: root.dismiss()
        ScaleLabel:
            size_hint_y: 0.14
            id: status
            markup: True
            font_size: '40sp'


<NewUserPopup@Popup>:
    title: 'Register #TODO not yet implemented'
    auto_dismiss: False
    on_enter: username.focus = True
    BoxLayout:
        orientation: 'vertical'
        TextInput:
            hint_text: "Player's name"
            id: username
            write_tab: False
            multiline: False
            height: self.minimum_height
            focus: True
            on_text_validate: email.focus = True
        TextInput:
            hint_text: "email address"
            id: email
            input_type: 'mail'
            write_tab: False
            multiline: False
            height: self.minimum_height
            on_text_validate: pin.focus = True
        TextInput:
            hint_text: "4-digit PIN number to enter games"
            id: pin
            input_type: 'number'
            write_tab: False
            multiline: False
            height: self.minimum_height
            on_text_validate: registerbutton.focus = True
        Button:
            id: registerbutton
            font_size: '20sp'
            bold: True
            text: 'Register'
            on_release: app.register_new_player()


<PinButton>
    font_size: '30sp'


<PinDigit>
    in_focus: False
    done: False
    text: '?' if self.in_focus else '*' if self.done else ' '
    font_size: '25sp'
    canvas.before:
        Color:
            rgba: 0.8, 0.8, 1.0, (1 if self.in_focus else 0)
        Line:
            width: 2
            rounded_rectangle: self.x, self.y, self.width, self.height, sp(10)
        Color:
            rgba: 0.1, 0.1, 0.3, (0 if self.in_focus else 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: sp(10), sp(10), sp(10), sp(10)


<PinPad>
    title: 'Please enter your PIN'
    orientation: 'vertical'
    pos_hint: {'top': 1, 'center_x': 0.5}
    size_hint: 1, 0.8
    ScaleLabel:
        size_hint_y: 0.1
        height: sp(40)
        font_size: sp(40)
        text: root.title
        size_hint_x: 1
    BoxLayout:
        cols: 4
        spacing: 10
        padding: 10
        height: sp(40)
        pos_hint: {'top': 0.9}
        size_hint: 1, 0.1
        orientation: 'horizontal'
        PinDigit:
            in_focus: True
        PinDigit:
        PinDigit:
        PinDigit:
    GridLayout:
        cols: 3
        orientation: 'horizontal'
        padding: 10
        size_hint_y: 0.6
        PinButton
            text: '7'
        PinButton
            text: '8'
        PinButton
            text: '9'
        PinButton
            text: '4'
        PinButton
            text: '5'
        PinButton
            text: '6'
        PinButton
            text: '1'
        PinButton
            text: '2'
        PinButton
            text: '3'
        PinButton
            text: '⇦'
        PinButton
            text: '0'
        PinButton:
            text: 'Cancel'


<PinPadPopup>:
    on_open: pinpad.reset()
    PinPad
        id: pinpad
'''