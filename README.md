# ZAPS Mahjong scorer

Riichi Mahjong score-keeper for Android (and possibly, eventually, iOS).

Home page: https://mj.bacchant.es/  - download the apk from there.

Right now, it's not possible to get this in the Android Play Store, because of this issue with the builder: https://github.com/kivy/python-for-android/issues/1219


### Prerequisites

[NanumGothic Bold & Regular fonts](https://fonts.google.com/specimen/Nanum+Gothic) (for the wind characters. Two special fonts just so that I can have the four Japanese wind characters. There must be a better way. Still, it's a nice-enough typeface.)

```
pip install requests kivy.deps.sdl2 kivy.deps.angle kivy.deps.glew kivy.deps.gstreamer kivy
```

### On the server

On the server: `pip install flask sqlalchemy authlib loginpass flask_login flask_migrate flask_sqlalchemy flask_wtf wtforms`

You'll need a config.py file with your own API keys. Here's [the temmplate](https://github.com/authlib/loginpass/blob/master/flask_example/config.py)

### Installing

Getting the development environment working was hard. I've included the dockerfile. I needed to tweak 
`/opt/buildozer/buildozer/targets/android.py` - my version in the repository. This dockerfile may not work for you. I'm still not sure how I got it working. Just got lucky, I think.


## Running the tests

So, there aren't any automated tests or anything. Just use it and try to break it. I'm really not a fan of test-driven development; but if you want to write tests for this and submit pull requests, please do go ahead.


## Built With

* [Python 3.6](https://python.org/) and should work fine with 3.7 (untested)
* [Kivy](https://kivy.org/)


## License

This project is licensed under the Affero GPL v3 Licence - see the [LICENSE](LICENSE) file for details


## Acknowledgments

* Thanks to Gemma Sakamoto for setting out her very stringent but reasonable requirements for a scoring app. Without that, this app wouldn't exist.
* Thanks to https://github.com/diegodukao/docker-python3-kivy-buildozer for the work on getting a build environment working. Without that, this app couldn't exist.
* Thanks to Mighel Grinberg for the [https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world](flask mega tutorial). Without that, I would not have got to grips with Flask.