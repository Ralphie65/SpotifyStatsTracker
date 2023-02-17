import time
import spotipy
# import json#
# import pprint#
import sqlite3
from flask import Flask, request, url_for, session, redirect, g, render_template, jsonify
from spotipy.oauth2 import SpotifyOAuth
#import pandas#

app = Flask(__name__)

app.secret_key = ""
app.config = ""
TOKEN_INFO = ""
conn = sqlite3.connect("trackstats.db")
cursor = conn.cursor()

@app.route('/')
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route('/redirect')
def redirectPage():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('getTracks', _external=True))


@app.route('/getTracks')
def getTracks():
    try:
        token_info = get_token()
    except Exception:
        print("user not logged in")
        return redirect("/")
    sp = spotipy.Spotify(auth=token_info['access_token'])
    userprofilelist = sp.current_user()
    username = userprofilelist.get('display_name')
    profilecheck = check_user(username)
    if profilecheck == 0:
        create_db()
        insert_db(username)
    data = get_db()
    return render_template("index.html", all_data=data)
    # return str(sp.current_user_saved_tracks(limit=50, offset=0)['items'][0])


@app.route('/current-playback')
def getplayback():
    try:
        token_info = get_token()
    except Exception:
        print("user not logged in")
        return redirect("/")
    sp = spotipy.Spotify(auth=token_info['access_token'])
    currentracklist = sp.currently_playing('US')
    cname = currentracklist['item']['name']
    ctime = currentracklist['progress_ms']
    cid = currentracklist['item']['id']
    url = currentracklist['item']['album']['images'][1]['url']
    cartist = currentracklist['item']['artists'][0]['name']
    #print(currentracklist)#
    #cresults = (cname, ctime, cid, url)
    return jsonify({'name': cname, 'time': ctime, 'artist': cartist, 'url': url})


@app.route('/skip-insert')
def skipinsert():
    try:
        token_info = get_token()
    except Exception:
        print("user not logged in")
        return redirect("/")
    sp = spotipy.Spotify(auth=token_info['access_token'])
    currentracklist = sp.currently_playing('US')
    print(currentracklist)
    cname = currentracklist['item']['name']
    ctime = currentracklist['progress_ms']
    cartist = currentracklist['item']['artists'][0]['name']
    cid = currentracklist['item']['id']
    url = currentracklist['item']['album']['images'][1]['url']
    #print(cname, ctime, cartist, cid)#
    cskip = 1
    insert_track(cname, cid, cartist, ctime, cskip)
    sp.next_track()
    return jsonify({'name': cname, 'time': ctime, 'artist': cartist, 'url': url})


def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        raise "exception"
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if is_expired:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id="",
        client_secret="",
        redirect_uri=url_for('redirectPage', _external=True),
        scope=('user-read-private', 'user-modify-playback-state', 'user-read-currently-playing'))


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('trackstats.db')
        cursor = db.cursor()
        cursor.execute("select user_name from users")
        cresult = cursor.fetchone()
        return cresult[0]


def create_db():
    conn = sqlite3.connect("trackstats.db")
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS tracks")
    cursor.execute("DROP TABLE IF EXISTS trackdetails")
    cursor.execute(
        "CREATE TABLE tracks (track_id text, user_name text, track_name text, artist text, times_played INTEGER, average_duration_played "
        "REAL, last_duration_played REAL, max_duration REAL, PRIMARY KEY (track_id))")
    cursor.execute(
        "CREATE TABLE trackdetails (auto_id INTEGER PRIMARY KEY AUTOINCREMENT, user_name text, track_name text, duration_played REAL, skipped INTEGER, track_id text)")
    # cursor.execute(
    #  "create table users (user_name text, total_time_listened real, favorite_artist text)")
    cursor.execute("CREATE TABLE users (user_name text)")
    conn.close()


def insert_db(username):
    conn = sqlite3.connect("trackstats.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (user_name) VALUES (?)", (username,))
    conn.commit()
    conn.close()


def check_user(username):
    conn = sqlite3.connect("trackstats.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM USERS WHERE user_name = (?)", (username,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return 1
    else:
        return 0


def load_tables(username):
    conn = sqlite3.connect("trackstats.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tracks")


def insert_track(cname, cid, cartist, ctime, cskip):  # TODO need to take my user out of here#
    conn = sqlite3.connect("trackstats.db")
    cursor = conn.cursor()
    print(cname, cid, cartist, ctime, cskip)
    cursor.execute("SELECT * FROM trackdetails WHERE track_id = (?)", (cid,))
    results = cursor.fetchone()  # if it exists in track details than we just log the new instance#
    if results:
        cursor.execute("INSERT INTO trackdetails(user_name, track_name, duration_played, skipped) values(?,?,?,?)",
                       ("ralphie65", cname, ctime, cskip))
        conn.commit()
        # TODO: Add update command here to tracks to update amount played and avg#
    else:
        cursor.execute("INSERT INTO trackdetails(user_name, track_name, duration_played, skipped) values(?,?,?,?)",
                       ("ralphie65", cname, ctime, cskip))
        conn.commit()
        cursor.execute("INSERT INTO tracks(track_id, user_name, track_name, artist, times_played, "
                       "average_duration_played, last_duration_played) values(?,?,?,?,1,0,?)",
                       (cid, "ralphie65", cname, cartist, ctime))
        conn.commit()
        t = cursor.execute("SELECT * FROM TRACKS")
        print(t)
        # cursor.execute("INSERT INTO trackdetails(user_name, track_name, duration_played, skipped) values(?,?,0,0)",#
        #  ("ralphie65", cname))#
        # conn.commit()#
        conn.close()
        return


@app.route('/refreshtracks')
def refreshtracks():
    conn = sqlite3.connect("trackstats.db")
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 5 * FROM tracksdetails")
    return cursor.fetchall()


conn.close()
