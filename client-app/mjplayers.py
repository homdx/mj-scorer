# -*- coding: utf-8 -*-
'''
Get player names, authentication and authorisation
'''


from kivy.properties import NumericProperty, ListProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput


WORD_LIST = \
    [1, 'how to use python'], [2, 'how to use kivy'], [3, 'to'], \
    [4, 'how to ...'], [5, 'abcdef'], [6, 'defghi'], [7, 'ghijkl']


class AutoComplete_TextInput(TextInput):
    '''
    auto-complete text box which offers suggestions based on
    substrings of entered text
    '''
    #txt_input = ObjectProperty()
    flt_list = ObjectProperty()
    word_list = ListProperty(WORD_LIST)
    prepared_word_list = []
    min_length_to_match = NumericProperty(3)

    def __init__(self, **kwargs):
        super(AutoComplete_TextInput, self).__init__(**kwargs)
        self.prepared_word_list = []
        for word in self.word_list:
            self.prepared_word_list.append(self.prepare_string(word[1]))

    def on_text(self, instance, value):
        # find all the occurrence of the substring
        #self.parent.ids.rv.data = []
        test = self.prepare_string(value)
        try:
            this_index = self.prepared_word_list.index(test)
        except ValueError:
            this_index = None
            if self.min_length_to_match > len(test):
                self.word_list = WORD_LIST
                return

        self.word_list = []
        actual_index = None
        for i in range(len(self.prepared_word_list)):
            if test in self.prepared_word_list[i]:
                if i == this_index:
                    actual_index = len(self.word_list)
                self.word_list.append(WORD_LIST[i])


        if actual_index is not None:
            # then in the next frame, find all SelectableLabel in rv
            # which is the list
            # self.parent.rv.children[0].children
            # find which one contains test (reverse order, as usual for kivy), and select it
            pass #TODO

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        key, key_str = keycode
        if key in (9, 13, 271):
            # TODO end it with whatever's selected, or if there's only one item
            # in list now, pick that
            print('bang 2')
        else:
            return super(AutoComplete_TextInput, self).keyboard_on_key_down(
                window, keycode, text, modifiers)

    @staticmethod
    def prepare_string(value):
        return value.replace(' ', '').replace('.', '').replace(',', '').lower()


class MJauto(BoxLayout):
    pass


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


class PlayerNames():

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
    spacing: 2

    AutoComplete_TextInput:
        readonly: False
        multiline: False
        id: txt_input
        table: users_table
        size_hint_y: None
        height: dp(30)

    MJTable:
        id: users_table
        txt_input: txt_input
        cols: 1
        data_items: txt_input.word_list


<LoginPopup@Popup>:

    title: 'Register this device'
    auto_dismiss: False
    on_open: username.focus = True

    BoxLayout:
        size_hint: 0.9, 0.5
        pos_hint: {'top': 1}
        orientation: 'vertical'

        Label:
            text: 'By registering this device with the server, your games will be stored there'

        TextInput:
            hint_text: "User name as registered"
            id: username
            write_tab: False
            multiline: False
            height: self.minimum_height
            focus: True
            on_text_validate: password.focus = True
        TextInput:
            hint_text: "Website password"
            id: password
            write_tab: False
            multiline: False
            height: self.minimum_height
            password: True
        Button:
            id: loginbutton
            font_size: '20sp'
            bold: True
            text: 'Login'
            on_release: root.dismiss() or app.register_device(username.text, password.text)
        Button:
            id: cancelbutton
            font_size: '20sp'
            bold: True
            text: 'Cancel'
            on_release: root.dismiss()


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