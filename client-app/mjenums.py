# -*- coding: utf-8 -*-
'''
enumerations and static objects used by most other modules
'''

from kivy.app import App

class Log():

    DEBUG = -1
    INFO = 0
    SCORE = 1
    UNUSUAL = 2
    ERROR = 99


class Result():

    TSUMO = 0
    RON = 1
    DRAW = 2
    MULTIPLE_RON = 3
    CHOMBO = -9999


class Ruleset():

    EMA2016 = 1
    WRC2017 = 2


class Rules():
    # defaults to EMA

    mangan_at_430 = False
    multiple_rons = True
    chombo_value = -200
    chombo_after_uma = True
    uma = [150, 50, -50, -150]
    # oka = 0 # currently oka is completely ignored, as neither of the implemented rulesets use it
    starting_points = 300
    riichi_abandoned_at_end = False


    def __init__(self, ruleset=Ruleset.WRC2017):
        if ruleset == Ruleset.EMA2016:
            pass
        elif ruleset == Ruleset.WRC2017:
            self.riichi_abandoned_at_end = True
            self.multiple_rons = False
            self.mangan_at_430 = True

        ids = App.get_running_app().root.ids
        ids.mangan_button.score = 2000 if self.mangan_at_430 else 1920
        ids.score_table.starting_points = self.starting_points
