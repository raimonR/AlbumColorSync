from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify
from skimage import io as imgio
from skimage.transform import resize
from sklearn.cluster import KMeans
from pathlib import Path
import numpy as np
import pandas as pd
from threading import Thread, Event


class Song:
    def __init__(self, song_label: str, album_url: str):
        self.song_id = song_label
        self.album_art_url = album_url
        self.accent_color = None


def update_token(uid: str, pwd: str, url: str, user: str, scope: str):
    auth = SpotifyOAuth(client_id=uid, client_secret=pwd, redirect_uri=url, scope=scope, username=user)
    token = auth.get_cached_token()
    if auth.is_token_expired(token_info=token) or token is None:
        auth.refresh_access_token(refresh_token=token['refresh_token'])
        token = auth.get_cached_token()
    return token['access_token']


def get_album_art_color(album_url: str):
    art = imgio.imread(album_url)
    art = resize(art, (125, 125), anti_aliasing=True, preserve_range=True)
    data = art.reshape(125*125, 3)
    kmeans = KMeans(n_clusters=5, random_state=0)
    clusters = kmeans.fit_predict(data)
    palette = kmeans.cluster_centers_

    color_idx = []
    for tmp in palette:
        clr = np.floor(tmp)
        mu = np.sqrt(np.mean(clr)**2 + np.mean(clr)**2)
        sig = np.sqrt(np.std(clr)**2 + np.std(clr)**2)
        color_idx.append(sig + 0.3*mu)

    rgb = palette[np.argmax(color_idx)]
    hex_color = '#%02X%02X%02X' % (int(rgb[0]), int(rgb[1]), int(rgb[2]))
    return hex_color


def get_current_song(access_token: str):
    client = Spotify(auth=access_token)
    tmp = client.current_user_playing_track()
    song = Song(song_label=tmp['item']['id'], album_url=tmp['item']['album']['images'][1]['url'])
    return song


def album_search(access_token: str, artist: str, album: str):
    client = Spotify(auth=access_token)
    res = client.search(q='album:' + album + ' artist:' + artist, limit=3, type='album')
    if res['albums']['total'] == 0:
        print("Not a valid album or artist.")
        return "Not a valid album or artist."
    else:
        potential_albums = {}
        for idx, albums in enumerate(res['albums']['items'], 1):
            potential_albums[idx] = {'name': albums['name'], 'artist': albums['artists'][0]['name'],
                                     'album_art': albums['images'][1]['url']}

        return potential_albums


def update_vinyl_list(album_artist, album_name, hex_color):
    vinyl_list = Path('../data/vinyl_list.pkl')
    if vinyl_list.is_file():
        df = pd.read_pickle(vinyl_list)
        df = df.append(other={'Artist': album_artist, 'Album': album_name, 'Album Color': hex_color}, ignore_index=True)
        df = df.drop_duplicates(keep='first')
        df = df.iloc[df.Artist.str.lower().argsort()]
        df = df.reset_index(drop=True)
        df.to_pickle(vinyl_list)
    else:
        df = pd.DataFrame(data={'Artist': album_artist, 'Album': album_name, 'Album Color': hex_color}, index=[0])
        df.to_pickle(vinyl_list)
    return


def get_current_song_color(access_token: str, old_song_id: str, current_color: str):
    client = Spotify(auth=access_token)
    is_playing = client.current_playback()['is_playing']
    if is_playing:
        tmp = client.current_user_playing_track()
        if tmp is None:
            return '#FFFFFF', ''
        song = Song(song_label=tmp['item']['id'], album_url=tmp['item']['album']['images'][1]['url'])

        if song.song_id != old_song_id:
            art = imgio.imread(song.album_art_url)
            art = resize(art, (125, 125), anti_aliasing=True, preserve_range=True)
            data = art.reshape(125*125, 3)
            kmeans = KMeans(n_clusters=5, random_state=0)
            clusters = kmeans.fit_predict(data)
            palette = kmeans.cluster_centers_

            color_idx = []
            for tmp in palette:
                clr = np.floor(tmp)
                mu = np.sqrt(np.mean(clr)**2 + np.mean(clr)**2)
                sig = np.sqrt(np.std(clr)**2 + np.std(clr)**2)
                color_idx.append(sig + 0.3*mu)

            song.accent_color = palette[np.argmax(color_idx)]

            return song.accent_color, song.song_id
        else:
            return current_color, old_song_id
    else:
        return '#333333', ''


def get_vinyl_list():
    df = pd.read_pickle('../data/vinyl_list.pkl')
    tmp = []
    for idx, row in enumerate(df.itertuples()):
        tmp.append([str(idx), '#' + str(idx), row.Artist, row.Album, row[-1]])
    return tmp
