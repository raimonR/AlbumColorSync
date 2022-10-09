from flask import Flask, render_template, redirect, url_for, jsonify, flash, request
from forms import VinylUpdateForm, AlbumSelectForm, SpotifyAlbumForm
from configparser import ConfigParser
from helpers import get_vinyl_list, update_token, album_search, update_vinyl_list, get_album_art_color
from time import sleep
from spotipy import Spotify
from threading import Thread, Event

app = Flask(__name__, template_folder='./templates/')


@app.route('/', methods=['GET'])
def home():
    title = 'Home'
    return render_template('base.html', title=title)


@app.route('/vinyl_list', methods=['GET', 'POST'])
def vinyl():
    global acs_tkn
    global album_search_results
    title = 'Vinyl List'
    df = get_vinyl_list()
    vinyl_update_form = VinylUpdateForm()
    spotify_album_form = SpotifyAlbumForm()
    if vinyl_update_form.validate_on_submit():
        # TODO: ADD ALBUM ADDITION HANDLING HERE
        results = album_search(acs_tkn, vinyl_update_form.data['artist_name'], vinyl_update_form.data['album_name'])
        album_art = [value['album_art'] for key, value in results.items()]
        spotify_album_form.album_choices.choices = [(key, value['name'] + ' - ' + value['artist']) for key, value in
                                                    results.items()]
        album_search_results = results
        return render_template('vinyl_list.html', title=title, vinyls=df, vinyl_update_form=vinyl_update_form,
                               spotify_album_form=spotify_album_form, art=album_art)

    if album_search_results is not None:
        spotify_album_form.album_choices.choices = [(key, value['name'] + ' - ' + value['artist']) for key, value in
                                                    album_search_results.items()]
    if spotify_album_form.validate_on_submit():
        selected_album = album_search_results[spotify_album_form.data['album_choices']]
        hex_color = get_album_art_color(selected_album['album_art'])
        update_vinyl_list(selected_album['artist'], selected_album['name'], hex_color)
        df = get_vinyl_list()
        album_search_results = None
        return render_template('vinyl_list.html', title=title, vinyls=df, vinyl_update_form=vinyl_update_form,
                               spotify_album_form=spotify_album_form)

    return render_template('vinyl_list.html', title=title, vinyls=df, vinyl_update_form=vinyl_update_form,
                           spotify_album_form=spotify_album_form)


@app.route('/_album_search', methods=['GET', 'POST'])
def spotify_album_search():
    title = 'Vinyl List'
    df = get_vinyl_list()
    vinyl_update_form = VinylUpdateForm()
    spotify_album_form = SpotifyAlbumForm()
    if spotify_album_form.validate_on_submit():
        print('here')
        return ''
    return jsonify(msg='Good')


@app.route('/playback', methods=['GET', 'POST'])
def playback():
    title = 'Playback'
    df = get_vinyl_list()
    form = AlbumSelectForm()
    form.album_choice.choices = [(idx, val[2] + ' - ' + val[3]) for idx, val in enumerate(df, 1)]
    if form.validate_on_submit():
        hex_color = df[form.album_choice.data - 1][-1]
        return redirect(url_for('vinyl_sync', album_color=hex_color))
    return render_template('playback.html', title=title, form=form)


@app.route('/color_sync/vinyl/<album_color>', methods=['GET'])
def vinyl_sync(album_color):
    title = 'Color Sync'
    return render_template('vinyl_sync.html', title=title, album_color=album_color)


@app.route('/color_sync/spotify', methods=['GET'])
def spotify_sync():
    title = 'Color Sync'
    return render_template('spotify_sync.html', title=title)


@app.route('/_spotify', methods=['GET', 'POST'])
def _spotify():
    global t
    global song_id
    global song_color
    global e
    global is_playing
    global acs_tkn
    client = Spotify(auth=acs_tkn)

    if not (client.devices() is None):
        tmp = []
        for dev in client.devices()['devices']:
            tmp.append(dev['is_active'])

        if not any(tmp):
            sleep(2)
            return jsonify(sync_color='#333333', song_id='', is_playing=False)

    if not t.is_alive():
        t = Thread(target=main_spotify, args=())
        t.start()

    if e.is_set() and t.is_alive():
        return jsonify(sync_color=song_color, song_id=song_id, is_playing=is_playing)
    elif not e.is_set():
        return jsonify(sync_color='#333333', song_id='', is_playing=is_playing)


@app.route('/_spotify_controls', methods=['GET', 'POST'])
def spotify_controls():
    # TODO: Need Spotify Premium to control fast-forward and fast-backward and pause/play
    global e
    global is_playing
    # client = Spotify(auth=acs_tkn)
    if request.method == 'POST':
        action = request.form['action']
        if action == 'forward':
            # client.next_track()
            return ''
        elif action == 'backward':
            # client.previous_track()
            return ''
        elif action == 'pause':
            # client.pause_playback()
            is_playing = False
            e.clear()
        elif action == 'play':
            # client.start_playback()
            is_playing = True
            e.set()

    return ''


def main_spotify():
    while True:
        global e
        global song_id
        global song_color
        while not e.is_set():
            sleep(1)

        client = Spotify(auth=acs_tkn)
        song = client.current_user_playing_track()
        if song is None:
            song_id = ''
            song_color = '#FFFFFF'
            sleep(10)
            continue
        else:
            new_id = song['item']['id']
            album_art_url = song['item']['album']['images'][1]['url']
            if song_id != new_id:
                song_color = get_album_art_color(album_art_url)
                song_id = new_id

            sleep(2)
    return


if __name__ == '__main__':
    config = ConfigParser()
    config.read('../data/config.txt')
    app.secret_key = config['flask_config']['csrf_key']
    id_ = config['configuration']['app_id']
    pwd = config['configuration']['app_password']
    url = config['configuration']['url']
    user = config['configuration']['username']
    scope = config['configuration']['scope']
    try:
        acs_tkn = update_token(id_, pwd, url, user, scope)
    except:
        print("offline")
        pass

    song_id = ''
    song_color = ''
    is_playing = True
    album_search_results = None

    t = Thread(target=main_spotify, args=())
    e = Event()
    e.set()

    app.jinja_env.globals.update(zip=zip)

    app.run()
