from glob import glob
import os
import time

def application(environ, start_response):

    basepath = 'webapps/wsgi/htdocs/'
    files = glob(basepath + '*.apk')
    try:
        newest = files[0][len(basepath):]
        version = newest.split('-')[1]
        filetime = time.strftime('%Y-%m-%d %H:%M', time.gmtime(os.path.getmtime(files[0])))
    except:
        newest = 'None available currently'
        version = '?'
        filetime = '?'

    output = '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>ZAPS Mahjong Scorer</title>
<link rel="icon" href="icon1.png">
</head>
<body style='background-color: #111; color: #dfd'>
<p>
You can download the Android pre-release test version of the ZAPS Mahjong Scorer here.
This is version <b>%s</b>, last updated %s GMT
</p>
<p><a style='color: #ccf' href='%s'>%s</a></p>
<p>For your phone to install this, you will probably need to temporarily turn on
"install from unknown sources" (Settings > Security).
Remember to turn it off again once installation is complete!</p>
<p>
During installation, Android Play Protect may warn you that it does not
recognise this apps's developer: select "Install anyway".
(<b>Warning</b>: if you select OK, it will abort the installation,
and may then be a bit sulky about installing this app in the future).
The app will take a few seconds to start.
</p>
<a href='%s' style='display: block'><img src='icon1.png' style='width: 20%%; height: auto'></a>
<section>
<h2>Recent updates</h2>
<ul>
<li>v0.2.0:
    <ul>
        <li>Restore any game in progress, on startup, after asking the user;
        <li>Wind rotation is correct now, when last hand is forgotten
        <li>Save game to local db at end of game
        <li>load score table from completed game in local game db
        <li>ask for confirmation before finishing game
    </ul>
<li>v0.1.5:
    <ul>
        <li>"Forget last hand" now works;
        <li>Add setting for English winds vs Japanese winds;
        <li>Developer tool: implemented profiler boolean setting
    </ul>
<li>v0.1.4: user can now set background colour from a choice of dark backgrounds
(no light background available yet)
</ul>
<h2># TODO (in descending priority)</h2>
<ul>
<li><h3>For v0.3:</h3>
<li>delete game from local game db
<li>server authentication
<li>store game on server
<li>get list of games from server
<li>retrieve a particular game from server
<li><h3>For v0.4:</h3>
<li>have a server-based list of IDs to choose players from, that mobile client can add to
<li><h3>For v?</h3>
<li>tournament and league mode on server
</ul>
<h3>Should these happen? Feedback welcome!</h3>
<ul>
<li>?optional enhanced scorecard like UKRC Open, with counter column, riichi bank, etc?
<li>?add game timer?
<li>?Add iPhone version?
</ul>
<h2>Older updates</h2>
<ul>
<li>v0.1.3: first alpha release
</ul>
</section>

</body>
</html>
''' % (version, filetime, newest, newest, newest)

    response_headers = [
        ('Content-Length', str(len(output))),
        ('Content-Type', 'text/html; charset=utf-8'),
    ]

    start_response('200 OK', response_headers)

    return [bytes(output, 'utf-8')]

