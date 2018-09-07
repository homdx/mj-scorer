# -*- coding: utf-8 -*-
'''
Get player names, authentication and authorisation
Thanks to /u/Saunfe on reddit for the basis for the autocomplete code
https://www.reddit.com/r/kivy/comments/99n2ct/anyone_having_idea_for_autocomplete_feature_in/
'''


from kivy.factory import Factory
from kivy.properties import NumericProperty, ListProperty, BooleanProperty, \
                            ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior


WORD_LIST = ['how to use python', 'how to use kivy', 'to', 'how to ...',
             'abcdef', 'defghi', 'ghijkl']


class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior,
                                 RecycleBoxLayout):
    ''' Adds selection and focus behaviour to the view. '''


class SelectableLabel(RecycleDataViewBehavior, Label):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            print('#TODO')
            self.parent.select_with_touch(self.index, touch)
            # TODO Need to assign it to something,
            # empty the text input, and close this dialogue
            return self.text, self.index

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected


class AutoComplete_TextInput(TextInput):
    '''
    auto-complete text box which offers suggestions based on
    substrings of entered text
    '''
    txt_input = ObjectProperty()
    flt_list = ObjectProperty()
    word_list = ListProperty(WORD_LIST)
    prepared_word_list = []

    min_length_to_match = NumericProperty(3)

    def __init__(self, **kwargs):
        super(AutoComplete_TextInput, self).__init__(**kwargs)
        for word in self.word_list:
            self.prepared_word_list.append(self.prepare_string(word))

    def on_text(self, instance, value):
        # find all the occurrence of the substring
        self.parent.ids.rv.data = []
        test = self.prepare_string(value)
        try:
            this_index = self.prepared_word_list.index(test)
        except ValueError:
            this_index = None
            if self.min_length_to_match > len(test):
                return

        display_data = []
        actual_index = None
        for i in range(len(self.word_list)):
            if test in self.prepared_word_list[i]:
                if i == this_index:
                    actual_index = len(display_data)
                display_data.append({'text': self.word_list[i]})

        self.parent.ids.rv.data = display_data

        if actual_index is not None:
            # then in the next frame, find all SelectableLabel in rv
            # which is the list
            # self.parent.rv.children[0].children
            # find which one contains test (reverse order, as usual for kivy), and select it
            pass #TODO

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        key, key_str = keycode
        print(key)
        if key in (13, 271):
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

    txt_input = ObjectProperty()
    rv = ObjectProperty()


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

    canvas:
        Color:
            rgba:(1, 1, 1, 1)
        Rectangle:
            pos: self.pos
            size: self.size

    orientation: 'vertical'
    spacing: 2
    txt_input: txt_input
    rv: rv

    AutoComplete_TextInput:
        readonly: False
        multiline: False
        id: txt_input
        size_hint_y: None
        height: dp(30)
    RecycleView:
        id: rv
        canvas:
            Color:
                rgba: 0,0,0,.2
            Line:
                rectangle: self.x +1 , self.y, self.width - 2, self.height -2
        bar_width: 10
        scroll_type:['bars']
        viewclass: 'SelectableLabel'
        SelectableRecycleBoxLayout:
            default_size: None, dp(24)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'
            multiselect: False
            spacing: dp(8)


<SelectableLabel>:
    # Draw a background to indicate selection
    color: 0,0,0,1
    canvas.before:
        Color:
            rgba: (0, 0, 1, .5) if self.selected else (1, 1, 1, 1)
        Rectangle:
            pos: self.pos
            size: self.size


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