# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView

from mjenums import Log


class ScoreSection(GridLayout):
    pass


class ScoreRow(GridLayout):
    data_items = ListProperty([0, 0, 0, 0, 0])
    row_type = StringProperty('deltas')

    @staticmethod
    def format_data(value, data_type, japanese_number_format=False):

        if data_type == 'headers':
            return '[b]%s[/b]' % value

        is_string = isinstance(value, str)

        if data_type == 'totals':
            if is_string:
                return '[b]%s[/b]' % value
            if value > 0:
                # positive total
                return '[b]%d[sub]00[/sub][/b]' % value
            if value == 0:
                # zero total
                return '[b]0[/b]'
            if japanese_number_format:
                # japanese, negative total
                return '[b][color=#F88]▲%d[sub]00[/sub][/color][/b]' % -value
            # western, negative total
            return '[b][color=#F88]%d[sub]00[/sub][/color][/b]' % value

        if data_type == 'deltas':
            if is_string:
                return value

            if value == 0:
                # zero delta
                return '[b][color=#888][sub]=[/sub][/color][/b]'

            if japanese_number_format:
                if value > 0:
                    # japanese, positive delta
                    return '[color=#AFA]+%d[sub]00[/sub][/color]' % value
                # Japanese, negative delta
                return '[color=#F88]▲%d[sub]00[/sub][/color]' % -value

            # Western number style
            if value > 0:
                # western, positive delta
                return '[color=#AFA]+%d[sub]00[/sub][/color]' % value

            # western, negative delta
            return '[color=#F88]%d[sub]00[/sub][/color]' % value


        if data_type == 'finaldeltas':
            if is_string:
                return value

            if value == 0:
                # zero final delta
                return '0'

            value = round(value / 10, 1)
            if japanese_number_format:
                if value > 0:
                    # japanese, positive final delta
                    return '[color=#AFA]+%.1f[/color]' % value
                # japanese, negative final delta
                return '[color=#F88]▲%.1f[/color]' % -value

            # Western number style
            if value > 0:
                # western, positive final delta
                return '[color=#AFA]+%.1f[/color]' % value

            # western, negative final delta
            return '[color=#F88]%.1f[/color]' % value


        # unknown combination of data type, number sign, and formatting style
        App.get_running_app().log(
            'Unkown data_type %s in ScoreRow.format_data' % str(type(data_type)),
            Log.ERROR)

        return str(value)


class ScoreRowSectionStart(ScoreRow):
    pass


class MjScoreTable(ScrollView):

    __selected_row = NumericProperty(0)


    def add_row(self, data_row, new_section):
        new_row = ScoreRowSectionStart() if new_section else ScoreRow()
        new_row.data_items = data_row
        new_row.data_type = 'deltas'
        self.ids.scoresection_hands.add_widget(new_row)
        return self.update_scores()


    def delete_row(self, row_number = -1):
        ''' Remove a row from the score table.
        Note that this call does not change the game situation at all;
        it's a purely cosmetic change to the score table presentation '''
        rows = self.ids.scoresection_hands
        row_to_remove = rows.children[-1 - row_number] # because the first child, is the last row. Blame kivy, not me
        App.get_running_app().log(
            Log.UNUSUAL,
            'Removed score table row:' + str(row_to_remove.data_items))
        rows.remove_widget(row_to_remove)


    def on_touch(self, ):
        App.get_running_app().log('TODO MjScoreTable.on_touch', Log.DEBUG)


    def reset(self):
        self.ids.scoresection_hands.clear_widgets()
        ids = ['running_totals', 'net_scores', 'scoretable_uma',
               'scoretable_chombos', 'scoretable_adjustments',
               'scoretable_final_totals']
        for row in ids:
            self.ids[row].data_items[1:] = [''] * 4


    def select_row(self, ):
        App.get_running_app().log('TODO MjScoreTable.select_row', Log.DEBUG)


    def update_scores(self):
        players = App.get_running_app().players
        for idx in range(4):
            self.ids.running_totals.data_items[idx + 1] = players[idx].score
        return self.ids.running_totals.data_items[1:]


    @staticmethod
    def get_kv():
        return '''

<ScoreRow>:
    cols: 5
    rows: 1
    size_hint: 1, None
    height: '25sp'
    ScaleLabel:
        markup: True
        text: ScoreRow.format_data(root.data_items[0], root.row_type, app.japanese_numbers)
    ScaleLabel:
        markup: True
        halign: 'right'
        text: ScoreRow.format_data(root.data_items[1], root.row_type, app.japanese_numbers)
    ScaleLabel:
        markup: True
        halign: 'right'
        text: ScoreRow.format_data(root.data_items[2], root.row_type, app.japanese_numbers)
    ScaleLabel:
        markup: True
        halign: 'right'
        text: ScoreRow.format_data(root.data_items[3], root.row_type, app.japanese_numbers)
    ScaleLabel:
        markup: True
        halign: 'right'
        text: ScoreRow.format_data(root.data_items[4], root.row_type, app.japanese_numbers)


<ScoreRowSectionStart>:
    canvas.after:
        Line:
            width: 1
            points:self.x, self.top, self.right, self.top

<ScoreSection>:
    size_hint: 1, None
    default_size_hint: 1, None
    cols: 1
    orientation: 'vertical'
    height: self.minimum_height

<MjScoreTable>:
    do_scroll_x: False
    do_scroll_y: True
    size_hint_x: 1
    starting_points: 1
    column_headings: ['hand', 'a', 'n', 'd', 's']

    GridLayout:

        orientation: 'vertical'
        size_hint: 1, None
        default_size_hint: 1, None
        cols: 1
        height: self.minimum_height

        ScoreSection:
            id: scoresection_header
            ScoreRow:
                id: scoretable_header
                row_type: 'headers'
                data_items: root.column_headings
            ScoreRow:
                id: scoretable_startpoints
                row_type: 'totals'
                data_items: ['start', root.starting_points, root.starting_points, root.starting_points, root.starting_points]

        ScoreSection:
            id: scoresection_hands

        ScoreSection:
            id: scoresection_running
            ScoreRowSectionStart:
                id: running_totals
                row_type: 'totals'
                height: '27sp'
                data_items: ['[b]Running Total[/b]', 0, 0, 0, 0]
                canvas.before:
                    Color:
                        rgba: 0, 0, 0.15, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size

        ScoreSection:
            id: scoresection_footer

            ScoreRow:
                id: net_scores
                row_type: 'finaldeltas'
                data_items: ['net score', 0, 0, 0, 0]

            ScoreRow:
                id: scoretable_uma
                row_type: 'finaldeltas'
                data_items: ['uma', 0, 0, 0, 0]

            ScoreRow:
                id: scoretable_chombos
                row_type: 'finaldeltas'
                data_items: ['chombos', 0, 0, 0, 0]

            ScoreRow:
                id: scoretable_adjustments
                row_type: 'finaldeltas'
                data_items: ['adjustments', 0, 0, 0, 0]

            ScoreRowSectionStart:
                id: scoretable_final_totals
                row_type: 'finaldeltas'
                height: '27sp'
                data_items: ['[b]Final score[/b]', 0, 0, 0, 0]
                canvas.before:
                    Color:
                        rgba: 0, 0, 0.25, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size
                canvas.after:
                    Line:
                        width: 1
                        points:self.x, self.top - 4, self.right, self.top - 4

'''
