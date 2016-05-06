#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, codecs, time, subprocess, threading, requests
# Set path directory so it can recognize modules from src
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

from urllib.parse import urlparse

from selenium.webdriver import Chrome, ChromeOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from src import database as db
from src.cover_art import SetCoverArt
from src.database import Item
from src.config import Config
from src.globals import *
from system_hotkey import SystemHotkey
from configparser import NoOptionError
import zmq

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# History of played things
played_engine = create_engine('sqlite:///playlist.db')
Session = sessionmaker()
played_engine.execute('PRAGMA encoding = "UTF-8"')
Base = declarative_base()
Item.metadata.create_all(played_engine)
Session.configure(bind=played_engine)
played = Session() # Video history

# Messages between this and chrome extension
config = Config()
port = config.configparser.getint('Network', 'port')
context = zmq.Context()
socket = context.socket(zmq.REP)
if port == 0:
    address = "tcp://*"
    address += ":" + str(socket.bind_to_random_port(address))
else:
    address = "tcp://*:%s" % port
    socket.bind(address)
with open("address.txt", 'w') as f:
    f.write(address)

# Chrome setup
options = ChromeOptions()
messaging_path = os.path.abspath(__file__ + '/../../Native messaging host/playlist app')
options.add_argument("--load-extension=" + messaging_path)

if not os.path.isdir('src/Extensions'):
    os.mkdir('src/Extensions')
# Add your extensions to the Extensions folder. Adblock is recommended
extensions = os.listdir('Extensions')
for extension in extensions:
    options.add_extension('Extensions/'+extension)

driver = Chrome(chrome_options=options)
driver.set_page_load_timeout(6)

try:
    p = subprocess.Popen('../Autoit script/volume changer.exe')
except FileNotFoundError:
    p = None


cover = SetCoverArt(RADIAN, RAINMETER) # Cover changer

thumbnails = ['http://img.youtube.com/vi/%s/maxresdefault.jpg', 'http://img.youtube.com/vi/%s/hqdefault.jpg', 'http://img.youtube.com/vi/%s/0.jpg'] # Thumbnail urls

# Select playlist
database = db.DatabaseHandler()
database.set_database(None, name=DATABASE) # Currently selected database

nx = False # If true song/video will change. Used by  callback()
item = None # The current item being played. See Item class in database.py for info
working = False # If True the video is working
wrk = 0 # Counter to check if the video is working
no_sound = 0 # Sound output check
running = True # Keeps the main loop running
pause = False # TODO: make a pause function
start = 0 # How long the song takes to start
stop = False # When true the program will initiate shutdown

auto_set_start = True # Set start time automatically if it is None or smaller than zero
override_start = False # Creates new start times all the time
thread = None # Thread that set cover art
message = 'OK'


# Set the rainmeter visualizer cover
def cover_configuration():
    pa = urlparse(driver.current_url)
    artist = pa.netloc
    query = pa.query
    if query == '' and 'youtube' not in artist:
        pass
    else:
        idx = query.find('v=') + 2
        if idx < 2:
            pass
        else:
            id = query[idx:idx+11]
            try:
                cover.set_coverart(item.name, 'Youtube', get_hqthumbnail(id))
                return
            except:
                pass
    cover.set_coverart(item.name, artist, None)


# Get Youtube thumbnail in the best quality possible with no API
def get_hqthumbnail(id):
    for tn in thumbnails:
        r = requests.get(tn % id, stream=True)
        if r.status_code != 404:
            return r.raw


# Close all windows except the one with the specified url
def close_windows(url):
    h = driver.window_handles
    if len(h) == 1:
        driver.switch_to.window(h[0])
        return
    saved_handle = h[0]
    for n in h:
        try:
            driver.switch_to.window(n)
            curr_url = driver.current_url
        except TimeoutException:
            driver.close()
            continue
        if curr_url != url:
            driver.close()
        else:
            saved_handle = n
    driver.switch_to.window(saved_handle)


# Install age verification bypass for Youtube
def install_script():
    driver.get('https://openuserjs.org/install/tfr/Bypass_YouTube_age_verification.user.js')
    time.sleep(1)
    handles = driver.window_handles
    for handle in handles:
        driver.switch_to.window(handle)
        curr_url = driver.current_url
        if 'chrome-extension://' in curr_url:
            try:
                elements = driver.find_elements_by_tag_name('input')
                for e in elements:
                    if e.get_attribute('value') == 'Install':
                        e.click()
                        break
            except NoSuchElementException:
                pass
    time.sleep(3)


# Triggers next_vid with a hotkey
def callback():
    global nx
    nx = True


# Change to next video/song
def next_vid():
    global item, start,thread
    if thread is not None:
        thread.join()
    item = database.choice()
    start = item.start
    played.add(Item(name=item.name, link=item.link, start=start))
    played.commit()
    try:
        driver.get(item.link)
        thread = threading.Thread(target=cover_configuration)
        thread.start()
    except TimeoutException:
        if not os.path.exists(item.link):
            next_vid()


def not_working():
    if item is not None:
        database.add_not_working(item)


def exit_chrome():
    global message
    if message != 'STOP':
        try:
            thread.join(3)
        except:
            pass
        cover.set_coverart('Visualizer', 'Radian', None)
        cover.quit()
        try:
            p.kill()
        except AttributeError:
            pass
        message = 'STOP'


def del_or_save(save):
    database.save_or_delete(item, save)


# Does not do anything
def pause_list():
    global pause
    pause = not pause

# Set hotkeys
hk = SystemHotkey()
hotkeys = [('next', lambda e: callback()), ('stop', lambda e:exit_chrome()), ('delete', lambda e: del_or_save(False)), ('save', lambda e: del_or_save(True))]
for key in hotkeys:
    try:
        hotkey = config.configparser.get('Hotkeys', key[0])
        hk.register(('control', hotkey), callback=key[1])
    except (NoOptionError, IndexError):
        pass

time.sleep(3)

close_windows(driver.current_url)

driver.switch_to.window(driver.window_handles[0])
driver.set_page_load_timeout(15)

msg = socket.recv_string()
socket.send_string('OK')
next_vid()

# Main loop that does everything
while running:
    try:
        while True:
            socket.recv_string(flags=1)
            socket.send_string(message)
    except:
        pass
    if msg =='OK':
        break
    wrk = 0
    working = False
    no_sound = 0
    video_playing = True
    t = time.time()
    if start is not None and start >= 0:
        print('wait time:', start)
        sound_check = 2
        while time.time() - t < start:
            try:
                msg = socket.recv_string(flags=1)
                if msg == 'NEXT':
                    socket.send_string(message)
                    next_vid()
                    break
                socket.send_string(message)
            except:
                continue
            if msg == 'OK':
                time.sleep(4)
                driver.quit()
                break
    else:
        sound_check = 10
    while video_playing:
        time.sleep(0.5)
        try:
            msg = socket.recv_string(flags=1)
            socket.send_string(message)
        except:
            continue
        if msg == 'OK':
            time.sleep(4)
            driver.quit()
            break
        if nx or msg == 'NEXT':
            print('wrk:', wrk, 'no sound:', no_sound)
            next_vid()
            nx = False
            break
        if msg == '"true"' and not working:
            if wrk >= 2:
                working = True
                if override_start or (auto_set_start and start is None or start < 0):
                    sound_check = no_sound + 2
                    print('time:', int(time.time() - t) - 2)
                    database.update_start(item, int(time.time() - t) - 2)
            wrk += 1
        if msg == '"false"':
            no_sound += 1
            if no_sound > sound_check:
                if wrk < 2:
                    print('Not working:', wrk)
                if not working:
                    not_working()
                next_vid()
                break
