from configparser import ConfigParser
import helpers as h
import numpy as np  # might remove later
import string
import skimage.io as imgio  # might remove later
from time import sleep
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("-f", "--function", choices=["playback", "update"], help="Play music or update vinyl list.")
parser.add_argument("-s", "--source", choices=["spotify", "vinyl"],
                    help="Indicate audio source for album color syncing.")
args = parser.parse_args()

config = ConfigParser()
config.read("../data/config.txt")
id_ = config["configuration"]["app_id"]
pwd = config["configuration"]["app_password"]
url = config["configuration"]["url"]
user = config["configuration"]["username"]
scope = config["configuration"]["scope"]

acs_tkn = h.update_token(id_, pwd, url, user, scope)

if args.function == "update":
    update = True
    while update:
        artist = input("Enter artist name you want to add: ")
        album = input("Enter name of album you want to add: ")
        album_art = h.update_vinyl_list(acs_tkn, artist, album)
        res = input("Add more? [Y]es/[N]o: ")
        res.lower().strip()
        if res[0] == "n":
            update = False
            res = input("Start playback? [Y]es/[N]o: ")
            res.lower().strip()
            if res[0] == "n":
                exit()

if args.source == "spotify":
    counter = 0
    while True:
        song = h.get_current_song(acs_tkn)
        counter += 1
        if song is not None:
            delta_t = song["item"]["duration_ms"] - song["progress_ms"]
            color = h.get_album_color(song)
            color = np.multiply(color, 255)
            s = song["item"]["name"]
            s = s.translate(str.maketrans('', '', string.punctuation))
            imgio.imsave(s + ".png", np.tile(color, (100, 100, 1)).astype(np.uint8))
            sleep(3)
        else:
            break
