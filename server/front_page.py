def front_page():
    from glob import glob
    import os
    import time
    basepath = 'webapps/wsgi/htdocs/static/'
    files = glob(basepath + '*.apk')
    try:
        newest = files[0][len(basepath):]
        version = newest.split('-')[1]
        filetime = time.strftime('%Y-%m-%d %H:%M', time.gmtime(os.path.getmtime(files[0])))
    except:
        newest = 'None available currently'
        version = '?'
        filetime = '?'

    return """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>ZAPS Mahjong Scorer</title>
<link rel="icon" href="/static/icon1.png">
<style>
a[href], a[href]:visited, a[href]:active {
    color: #FFB;
    border: 3px outset #333;
    display: inline-block;
    text-decoration: none;
}
a[href]:active {
    border: 3px inset;
}
body {
    background-color: #111;
    color: #dfd
}
</style>
</head>
<body>
<p>
You can download the Android pre-release test version of the
<a href='https://github.com/ApplySci/mj-scorer'>open-source</a>
ZAPS Mahjong Scorer here.
This is version <b>%s</b>, last updated %s GMT
</p>
<p><a href='/static/%s'>%s</a></p>
<p>For your phone to install this, you will probably need to temporarily turn on
"install from unknown sources" (Settings > Security).
Remember to turn it off again once installation is complete!</p>
<p>If you have any suggestions, questions, bugs, please
<a href='https://github.com/ApplySci/mj-scorer/issues'>raise them as an issue on github</a>
During installation, Android Play Protect may warn you that it does not
recognise this apps's developer: select "Install anyway".
(<b>Warning</b>: if you select OK, it will abort the installation,
and may then be a bit sulky about installing this app in the future).
The app will take a few seconds to start.
</p>
<a href='/static/%s' style='display: block; border: none;'><img src='/static/icon1.png' style='width: 20%%; height: auto'></a>
<section>
<h2>Recent updates</h2>
<ul>
<li>v0.2.1:
    <ul>
        <li>Save multiple unfinished games to database
        <li>EMA starting points are 30k, not 25k
        <li>Clearer riichi stick silhouette
        <li>add in_progress status to game db description string
    </ul>
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
        <li>Enable upload/download of games in progress for later resumption from same or different device
        <li>delete game from local game db
        <li>store game (finished or in progress) on server, in a named store protected by a user-chosen password
        <li>get list of games from server in a named store, once store's password is entered
        <li>retrieve a particular game from server
        <li><h3>For v0.4:</h3>
        <li>have a server-based list of IDs to choose players from, that mobile client can add to
        <li>server authentication by ID
        <li><h3>For v?</h3>
        <li>tournament and league mode on server
        <li>Add iPhone version
</ul>
<h3>Should these happen? Feedback welcome!</h3>
<ul>
<li>?optional enhanced scorecard like UKRC Open, with counter column, riichi bank, etc?
<li>?add game timer?
</ul>
<h2>Older updates</h2>
<ul>
<li>v0.1.3: first alpha release
</ul>
</section>

</body>
</html>
""" % (version, filetime, newest, newest, newest)
