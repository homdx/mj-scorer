# ZAPS Mahjong scorer

Riichi Mahjong score-keeper for Android (and possibly, eventually, iOS).

### To run the app on an android phone

Home page: [https://mj.bacchant.es/](https://mj.bacchant.es/)  - download the apk from there. If you only want to use the client app, that's all you need to do. This open-source repository is for people who want to see how the innards work, contribute to development, and/or run their own game server.

Right now, it's not possible to put the app onto the Android Play Store, because of [this issue with the packager](https://github.com/kivy/python-for-android/issues/1219)

### To develop and/or run the client app locally

This is tested on Windows; almost certainly works on any device with a GUI and Python)

You only need the client-app directory (and directories it contains).

You'll need [Python 3.6](http://www.python.org/) (almost certainly works with Python 3.7 too, but untested). 

Get [NanumGothic Bold & Regular fonts](https://fonts.google.com/specimen/Nanum+Gothic) for the wind characters. Two special fonts just so that I can have the four Japanese wind characters. There must be a better way. Still, it's a nice-enough typeface.

```
pip install requests kivy.deps.sdl2 kivy.deps.angle \
    kivy.deps.glew kivy.deps.gstreamer kivy
```

Then run `python main.py` to start the app.


### To develop and/or run the server

Note that the server is barely doing anything yet, so there's not much functionality to test. This is where most of the development needs to happen.

You'll need [Python 3.6](http://www.python.org/) (almost certainly works with Python 3.7 too, but untested). 

```
pip install flask sqlalchemy authlib loginpass flask_login \
    flask_migrate flask_sqlalchemy flask_wtf wtforms \
    flask-httpauth
```

You'll need a `config.py` file with your own API keys. Copy `config.py.template` to `config.py` and fill in accordingly. Do the same with `salt.py.template` and `salt.py` . Note that the client-app will need an identical `salt.py`

The server needs the files and sub-directories in the `server` directory. From that directory, at the command line, do:
```python  
flask db init  
flask db migrate  
flask db upgrade  
```
to initialise the database, and ```flask run``` to run the server on localhost:5000.


### Packaging

The client app runs fine on windows from the command line without being packaged, so that's fine for development and testing. And the server-side doesn't need packaging, and can (for development) be run from the command line with `flask run`.

Packaging is only needed for getting the app onto an android device. Getting the packaging environment working was hard. I've included the dockerfile.

I needed to tweak `/opt/buildozer/buildozer/targets/android.py` - my version in the repository. This dockerfile may not work for you. I'm still not sure how I got it working. Just got lucky, I think. Anyway, you don't need a working packaging environment to develop this app. Just test on your development machine. I can package stuff up on request.


## Running the tests

So, there aren't any automated tests or anything. Just use it and try to break it. I'm really not a fan of test-driven development; but if you want to write tests for this and submit pull requests, please do go ahead.


## Built With

* [Python 3.6](https://python.org/) and should work fine with 3.7 (untested)
* [Kivy](https://kivy.org/)


## License

This project is licensed under the Affero GPL v3 Licence - see the [LICENSE](LICENSE) file for details


## Thanks

* Thanks to Gemma Sakamoto for setting out her very stringent but reasonable requirements for a scoring app. Without that, this app wouldn't exist.
* Thanks to [diegodukao](https://github.com/diegodukao/docker-python3-kivy-buildozer) for the work on getting a build environment working. Without that, this app couldn't exist.
* Thanks to Miguel Grinberg for his [flask tutorial series](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world). Without that, I would not have got to grips with Flask.