import pdb
import time
import spotipy
# import json#
# import pprint#
import sqlite3
#import pdp#
from flask import Flask, request, url_for, session, redirect, g, render_template, jsonify
from spotipy.oauth2 import SpotifyOAuth
from environs import Env
#import pandas#

app = Flask(__name__)

env = Env()
env.read_env()  # load the environment variables from the .env file

app.secret_key = env('app.secret_key')
app.config[env('config_name')] = env('cookie_name')
TOKEN_INFO = env('token')
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
    user_profile_pic = userprofilelist['images'][0]['url']
    profilecheck = check_user(username)
    if profilecheck == 0:
        create_db()
        insert_db(username, user_profile_pic)
    user_name, user_prof_pic = get_db()
    return render_template("index.html", user_profile_data=(user_name, user_profile_pic))


@app.route('/current-playback')
def getplayback():
    try:
        token_info = get_token()
    except Exception:
        print("user not logged in")
        return redirect("/")
    sp = spotipy.Spotify(auth=token_info['access_token'])
    #sp.start_playback()#
    #pdb.set_trace()#
    currentracklist = sp.currently_playing('US')
    if currentracklist is None:
        lastdevice = get_devices()
        if lastdevice != 0:
            sp.start_playback()
        return jsonify({})
    cname = currentracklist['item']['name']
    ctime = currentracklist['progress_ms']
    cid = currentracklist['item']['id']
    url = currentracklist['item']['album']['images'][1]['url']
    cartist = currentracklist['item']['artists'][0]['name']
    mtime = duration_ms = currentracklist['item']['duration_ms']
    #print(sp.me())#
    return jsonify({'name': cname, 'time': ctime, 'mtime': mtime, 'artist': cartist, 'url': url})


@app.route('/skip-insert')
def skipinsert():
    try:
        token_info = get_token()
    except Exception:
        print("user not logged in")
        return redirect("/")
    sp = spotipy.Spotify(auth=token_info['access_token'])
    currentracklist = sp.currently_playing('US')
    api_helper(token_info, True)
    sp.next_track()
    return api_helper(token_info, False)

@app.route('/pause-song')
def pausesong():
    try:
        token_info = get_token()
    except Exception:
        print("user not logged in")
        return redirect("/")
    sp = spotipy.Spotify(auth=token_info['access_token'])
    results = api_helper(token_info, False)
    sp.pause_playback()
    #return jsonify({'name': cname, 'time': ctime, 'artist': cartist, 'url': url})#
    return results

@app.route('/go-back')
def goback():
    try:
        token_info = get_token()
    except Exception:
        print("user not logged in")
        return redirect("/")
    sp = spotipy.Spotify(auth=token_info['access_token'])
    currentracklist = sp.currently_playing('US')
    cname = currentracklist['item']['name']
    ctime = currentracklist['progress_ms']
    cartist = currentracklist['item']['artists'][0]['name']
    cid = currentracklist['item']['id']
    url = currentracklist['item']['album']['images'][1]['url']
    #print(cname, ctime, cartist, cid)#
    cskip = 1
    insert_track(cname, cid, cartist, ctime, cskip)
    sp.previous_track()
    currentracklist = sp.currently_playing('US')
    cname = currentracklist['item']['name']
    ctime = currentracklist['progress_ms']
    cartist = currentracklist['item']['artists'][0]['name']
    cid = currentracklist['item']['id']
    url = currentracklist['item']['album']['images'][1]['url']
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
        client_id=env('client_id'),
        client_secret=env('client_secret'),
        redirect_uri=url_for('redirectPage', _external=True),
        scope=('user-read-private', 'user-modify-playback-state', 'user-read-currently-playing', 'user-read-playback-state', 'user-read-recently-played','app-remote-control', 'streaming'))


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('trackstats.db')
        cursor = db.cursor()
        cursor.execute("SELECT user_name, user_prof_pic FROM userdetails")
        cresult = cursor.fetchone()
        return cresult

def create_db(): #create all the tables#
    conn = sqlite3.connect("trackstats.db")
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS tracks")
    cursor.execute("DROP TABLE IF EXISTS trackdetails")
    cursor.execute("DROP TABLE IF EXISTS userdetails")
    cursor.execute(
        "CREATE TABLE tracks (track_url text, track_id text, user_name text, track_name text, artist text, times_played INTEGER, average_duration_played "
        "REAL, last_duration_played REAL, max_duration REAL, PRIMARY KEY (track_id))")
    cursor.execute(
        "CREATE TABLE trackdetails (auto_id INTEGER PRIMARY KEY AUTOINCREMENT, user_name text, track_name text, duration_played REAL, skipped INTEGER, track_id text)")
    cursor.execute("CREATE TABLE users (user_name text)")
    cursor.execute("CREATE TABLE userdetails (user_name text, total_time_listened real, user_prof_pic text)")
    conn.close()


def insert_db(username, purl): #inserts send username into database#
    conn = sqlite3.connect("trackstats.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (user_name) VALUES (?)", (username,))
    cursor.execute("INSERT INTO userdetails (user_name, total_time_listened, user_prof_pic) VALUES (?,?,?)", (username,0,purl))
    conn.commit()
    conn.close()


def check_user(username): #check if sent paramater user matches the user in the users table#
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

def get_devices(): #get list of devices used on spotify, and returns last used#
    try:
        token_info = get_token()
    except Exception:
        print("user not logged in")
        return redirect("/")
    sp = spotipy.Spotify(auth=token_info['access_token'])
    devices = sp.devices()
    if devices['devices']: #if there are any devices, return last used#
        device_id = devices['devices'][0]['id']
        return device_id
    else:
        return 0

def insert_track(cname, cid, cartist, ctime, cskip, mtime, urlmini):
    conn = sqlite3.connect("trackstats.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM USERS LIMIT 1")
    row = cursor.fetchone()
    username = row[0]
    cursor.execute("SELECT * FROM trackdetails WHERE track_id = (?)", (cid,))
    results = cursor.fetchone()  # if it exists in track details than we just log the new instance#
    if results:
        cursor.execute("INSERT INTO trackdetails(user_name, track_name, duration_played, skipped, track_id) values(?,?,?,?,?)",
                       (username, cname, ctime, cskip, cid))
        conn.commit()
        cursor.execute("UPDATE tracks SET times_played = times_played + 1, average_duration_played = "
                       "(average_duration_played * times_played + ?) / (times_played + 1) WHERE track_id = ?",
                       (ctime, cid))
        conn.commit()
        conn.close()
    else:
        cursor.execute("INSERT INTO trackdetails(user_name, track_name, duration_played, skipped, track_id) values(?,?,?,?,?)",
                       (username, cname, ctime, cskip, cid))
        conn.commit()
        cursor.execute("INSERT INTO tracks(track_url,track_id, user_name, track_name, artist, times_played, "
                       "average_duration_played, last_duration_played, max_duration) values(?,?,?,?,?,1,?,?,?)",
                       (urlmini, cid, username, cname, cartist, ctime, ctime, mtime))
        conn.commit()
        conn.close()
        return

def api_helper(token_info, insert):
    sp = spotipy.Spotify(auth=token_info['access_token'])
    currentracklist = sp.currently_playing('US')
    cname = currentracklist['item']['name']
    ctime = currentracklist['progress_ms']
    cartist = currentracklist['item']['artists'][0]['name']
    cid = currentracklist['item']['id']
    url = currentracklist['item']['album']['images'][1]['url']
    mtime = currentracklist['item']['duration_ms']
    urlmini = currentracklist['item']['album']['images'][2]['url']
    cskip = 1
    results = jsonify({'name': cname, 'time': ctime, 'artist': cartist, 'url': url})
    if insert:
        insert_track(cname, cid, cartist, ctime, cskip, mtime, urlmini)
    return results



@app.route('/refreshtracks')
def refreshtracks():
    conn = sqlite3.connect("trackstats.db")
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 5 * FROM tracksdetails")
    conn.close()
    return cursor.fetchall()


@app.route('/toplist')
def toplist():
    conn = sqlite3.connect("trackstats.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tracks")
    rows = cursor.fetchall()

    # create array of dictionaries
    items = []
    for row in rows:
        item = {
            'track_url': row[0],
           # 'track_id': row[1],#
            #'username': row[2],#
            'track_name': row[3],
            'artist': row[4],
            'times_played': row[5],
            'average_duration_played': row[6],
            'last_duration_played': row[7],
            'max_duration': row[8]
        }
        items.append(item)
    conn.close()
    return jsonify(items)

conn.close()
