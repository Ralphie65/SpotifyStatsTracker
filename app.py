import time
import spotipy
import json
# import pprint#
import sqlite3
from flask import Flask, request, url_for, session, redirect, g, render_template
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)

app.secret_key = ""
app.config['']
TOKEN_INFO = ""
conn = sqlite3.connect("trackstats.db")
cursor = conn.cursor()


# cursor.execute("create table tracks (track_name text, artist text, times_played integer, average_duration_played "
# "real, last_duration_played real)")


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
    except:
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
    return render_template("index.html", all_data= data)
    #return str(sp.current_user_saved_tracks(limit=50, offset=0)['items'][0])


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
        scope='user-read-private')


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('trackstats.db')
        cursor = db.cursor()
        cursor.execute("select user_name from users")
        return cursor.fetchall()


def create_db():
    conn = sqlite3.connect("trackstats.db")
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS tracks")
    cursor.execute("DROP TABLE IF EXISTS trackdetails")
    cursor.execute(
        "CREATE TABLE tracks (user_name text, track_name text, artist text, times_played INTEGER, average_duration_played "
        "REAL, last_duration_played REAL)")
    cursor.execute("CREATE TABLE trackdetails (user_name text, track_name text, duration_played REAL, skipped INTEGER)")
    #cursor.execute(
      #  "create table users (user_name text, total_time_listened real, favorite_artist text)")
    cursor.execute("create table users (user_name text)")
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


@app.route('/refreshtracks')
def refreshtracks():
    conn = sqlite3.connect("trackstats.db")
    cursor = conn.cursor()
    cursor.execute()


conn.close()
