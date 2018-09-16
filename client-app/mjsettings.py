# -*- coding: utf-8 -*-
'''
contains the settings structure as a dict, to create the settings
screen in kivy. The rest of the settings handling is in main.py, but could
be moved here
'''
import json

from kivy.app import App

def settings_json():
    button_text, setting_text, desc_text = App.get_running_app().registration_text()
    return json.dumps([
    {'type': 'title', 'title': 'Settings'},
    {'type': 'options',
     'title': 'background colour',
     'desc': 'Click the colour to get a list of background colours to choose from',
     'section': 'main',
     'key': 'bg_colour',
     'options': ['black',
                 'dark blue',
                 'dark green',
                 'dark grey',
                 'dark red']
    },
    {'type': 'bool',
     'title': 'Use Japanese-style number signs instead of Western',
     'section': 'main',
     'desc': 'Positive numbers are prefixed with +; negative numbers and prefixed with ▲',
     'key': 'japanese_numbers',
    },
    {'type': 'bool',
     'title': 'Use Japanese wind labels instead of English',
     'section': 'main',
     'desc': 'Another purely cosmetic setting: use 東,南,西,北 instead of E,S,W,N',
     'key': 'japanese_winds',
    },
    {'type': 'bool',
     'title': 'send games to server',
     'section': 'main',
     'desc': 'if turned off, no network is used, and games are only scored on this device',
     'key': 'use_server',
    },
    {'type': 'string',
     'title': 'path to server',
     'section': 'main',
     'desc': 'include protocol, server, and trailing slash , e.g. https://mj.bacchant.es/ . You will probably need to re-register this device if you change this, with your username and password for the new server ',
     'key': 'server_path',
    },
    {'type': 'button',
     'title': setting_text,
     'section': 'main',
     'buttons': [{'title': button_text, 'id': 'register_device'}],
     'desc': desc_text,
     'key': 'register'
    },
    ])

'''
    {'type': 'button',
     'title': 'Open browser',
     'section': 'main',
     'buttons': [{'title': 'Open browser', 'id': 'browser'}],
     'desc': 'Go to the website now to resgister',
     'key': 'auth_browser'
    },
    {'type': 'string',
     'title': 'Name of the game store to use',
     'section': 'unused',
     'desc': 'Create a store using a web-browser at https://mj.bacchant.es/ , and get the password there too',
     'key': 'api_store',
    },
    {'type': 'password',
     'title': 'Password for store',
     'section': 'unused',
     'desc': '',
     'key': 'api_password',
    },
    {'type': 'bool',
     'title': 'Developer option: profiling',
     'section': 'unused',
     'desc': 'Use code profiling to log CPU by call: this will create a file to be analysed by the developers. It will take effect when the app is next started.',
     'key': 'profiling',
    },
'''