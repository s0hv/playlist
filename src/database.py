#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy import Integer, Column, String, INTEGER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src import config as cfg
import random, math, os, itertools

Base = declarative_base()


class Item(Base):
    __tablename__ = "playlist"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    link = Column(String)
    start = Column(INTEGER, default=-1)  # The length of the video in seconds.
    # If 0 or less the program will automatically assign one when the video is played.
    play_times = Column(INTEGER, default=0)  # How many times the video has been played


class DatabaseHandler(object):
    def __init__(self):
        if not os.path.isdir('../playlists'):
            os.mkdir('../playlists')

        # All the different databases. Not sure if it's good to initialize them now though
        self.full, self.playing, self.onhold, self.saved, self.deleted = None, None, None, None, None
        self.engine_full, self.engine_onhold, self.engine_playing = None, None, None  # DB engines
        self.list_size = 0  # The size of the playlist
        self.not_working = None  # Another database that stores songs that might not work
        self.wd = None  # Working dir
        self.config = cfg.Config()  # The config handler

    # Set the active database
    def set_database(self, path=None, create=False, name=None):
        if name is not None:
            path = self.config.configparser.get('Playlists', name)
        elif path is None:
            print("No database specified in the parameters")

        self.wd = path
        print('%splaylist.db' % path)
        self.engine_full = create_engine('sqlite:///%splaylist.db' % path)  # , echo=True)
        self.engine_playing = create_engine('sqlite:///%splaylist_playing.db' % path)  # , echo=True)
        self.engine_onhold = create_engine('sqlite:///%splaylist_onhold.db' % path)  # , echo=True)

        Session = sessionmaker()
        Session2 = sessionmaker()
        Session3 = sessionmaker()

        # Create new database with the provided information
        if create:
            try:
                if not os.path.exists(path):
                    os.mkdir(path)
            except WindowsError:
                return False
            Item.metadata.create_all(self.engine_full)
            Item.metadata.create_all(self.engine_playing)
            Item.metadata.create_all(self.engine_onhold)

        # Force UTF-8 encoding
        self.engine_full.execute('PRAGMA encoding = "UTF-8"')
        self.engine_playing.execute('PRAGMA encoding = "UTF-8"')
        self.engine_onhold.execute('PRAGMA encoding = "UTF-8"')

        Session.configure(bind=self.engine_full)
        Session2.configure(bind=self.engine_playing)
        Session3.configure(bind=self.engine_onhold)

        # The main 3 databases
        self.full = Session()
        self.playing = Session2()
        self.onhold = Session3()

        # Set how many items should be in the playing.db.
        self.list_size = math.ceil(
            len(list(self.full.query(Item))) * self.config.configparser.getfloat('List Options', 'playing_size'))
        print(self.list_size)

    # Gets an unused id in the database
    @staticmethod
    def get_id(session, multiple=False):
        items = session.query(Item)
        ids = []
        idx = 1

        for item in items:
            row_id = item.id
            if row_id != idx:
                if not multiple:
                    return idx
                else:
                    ids += idx
            idx += 1

        if not multiple:
            return None
        else:
            return ids

    def check_size(self):
        size = len(list(self.playing.query(Item)))

        if size <= self.list_size:
            return True
        return False

    # Get a random item from the playlist
    @staticmethod
    def get_random(session):
        q = list(session.query(Item))
        items = q[0:math.ceil(len(q) * 0.25)]
        sorted(items, key=lambda i: (i.play_times is not None, i))
        sorted_items = [x for x in items if x.play_times == items[0].play_times]
        return random.choice(sorted_items)

    # Create the item to an available id slot
    def create_item(self, name, link, session, start=-1, play_times=0):
        item = Item(link=link, name=name, start=start, play_times=play_times)
        i = self.get_id(session)
        if i is not None:
            item.id = i
        return item

    # Uses create_item to add an item to a database. Does not commit anything
    def _add_item(self, session, item=None, name='', link=''):
        if item is None:
            if link == '':
                return False
            item = self.create_item(name, link, session)
        session.add(item)

    # Delete item by id
    @staticmethod
    def delete(engine, row_id):
        engine.execute('DELETE FROM playlist where ID = ' + str(row_id))

    # Checks if everything is OK
    def check_integrity(self):
        if self.playing is None:
            return False
        self.full.commit()
        self.playing.commit()
        self.onhold.commit()
        length = len(list(self.full.query(Item)))
        p_length = len(list(self.playing.query(Item)))
        o_length = len(list(self.onhold.query(Item)))
        if length == o_length + p_length:
            return True
        else:
            return False

    # return a random item drom the beginning of the playing DB.
    def choice(self):
        assert self.playing is not None, "No database selected"

        row = self.get_random(self.playing)
        item = Item(link=row.link, name=row.name, start=row.start, play_times=row.play_times)
        print(str(item.link), str(item.name), str(item.play_times))
        self.playing.delete(row)
        self.onhold.add(item)

        if self.check_size():
            items = list(self.onhold.query(Item))
            items = items[0:math.ceil(len(items) * 0.25)]
            row2 = random.choice(items)
            self.playing.add(Item(name=row2.name, link=row2.link, start=row2.start, play_times=row2.play_times))
            self.onhold.delete(row2)

        self.playing.commit()
        self.onhold.commit()
        return row

    def connect_not_working(self):
        if self.not_working is None:
            engine_notworking = create_engine('sqlite:///%splaylist_notworking.db' % self.wd)
            Session4 = sessionmaker()
            Base.metadata.create_all(engine_notworking)
            Session4.configure(bind=engine_notworking)
            self.not_working = Session4()

    def connect_saved(self):
        if self.saved is None:
            engine_saved = create_engine('sqlite:///%splaylist_saved.db' % self.wd)
            Session5 = sessionmaker()
            Base.metadata.create_all(engine_saved)
            Session5.configure(bind=engine_saved)
            self.saved = Session5()

    def connect_deleted(self):
        if self.deleted is None:
            engine_deleted = create_engine('sqlite:///%splaylist_deleted.db' % self.wd)
            Session6 = sessionmaker()
            Base.metadata.create_all(engine_deleted)
            Session6.configure(bind=engine_deleted)
            self.deleted = Session6()

    # Connect to all databases if it hasn't been done yet
    def connect_others(self):
        if self.wd is None:
            print("Not connected to a database")
            return

        self.connect_not_working()
        self.connect_deleted()
        self.connect_saved()

    def add_not_working(self, item):
        if self.wd is None:
            return

        self.connect_not_working()

        link = item.link
        name = item.name
        itm = (Item(name=name, link=link, start=item.start))
        self.not_working.add(itm)
        self.not_working.commit()

        return True

    # Do set delete_item to True when the playlist is not running
    # TODO delete_item
    def save_or_delete(self, item: Item, save: bool, delete_item: bool = False):
        item = Item(link=item.link, name=item.name, start=item.start, play_times=item.play_times)

        if save:
            self.connect_saved()
            self.saved.add(item)
            self.saved.commit()

        elif not save:
            self.connect_deleted()
            self.deleted.add(item)
            self.deleted.commit()

            if delete_item:
                self.delete_items(item)

    # Deletes the list or query of items from.
    def delete_items(self, items=None):
        assert self.check_integrity() is True, "Playlist might be corrupted. Aborting"

        if items is None:
            print("No items given.")
            return

        if self.full is None:
            return

        full_query = self.full.query(Item)
        onhold_query = self.onhold.query(Item)
        playing_query = self.playing.query(Item)

        amount = len(list(full_query))
        deleted_items = 0

        # TODO remove items from all available databases
        for item in items:
            self.full.delete(full_query.filter_by(link=item.link, name=item.name).first())
            delete = onhold_query.filter_by(link=item.link, name=item.name).first()
            if delete is None:
                delete = playing_query.filter_by(link=item.link, name=item.name).first()
                assert delete is not None, "Item not found in playlists. Playlist might be corrupted"
                self.playing.delete(delete)
            else:
                self.onhold.delete(delete)

            deleted_items += 1
            print("Deleted:", item.name, item.link)

        self.full.commit()
        self.onhold.commit()
        self.playing.commit()

        print("Successfully deleted", str(deleted_items) + "/" + str(amount))

    @staticmethod
    # Merges a DB to another DB.
    def add_from_db(self, source, target, duplicates=False):
        print("Too lazy to finish this.")
        return
        # TODO Everything

    # Runs the commit command for all databases
    def commit_all(self):
        self.playing.commit()
        self.full.commit()
        self.onhold.commit()
        if self.deleted is not None:
            self.deleted.commit()
        if self.not_working is not None:
            self.not_working.commit()
        if self.saved is not None:
            self.saved.commit()

    # Pretty self explanatory
    def add_new_item(self, link, name):
        item = Item(link=link, name=name)
        item2 = Item(link=link, name=name)
        self.full.add(item)
        self.full.commit()
        self.playing.add(item2)
        self.playing.commit()

    # TODO A function that resets the id values of the selected DB since the id grows all the time

    # Changes the start if an item to the one specified in the parameter start
    def update_start(self, item, start):
        f = self.full.query(Item).filter_by(link=item.link, name=item.name)
        o = self.onhold.query(Item).filter_by(link=item.link, name=item.name)
        p = self.playing.query(Item).filter_by(link=item.link, name=item.name)
        if len(list(o)) == 0 and len(list(p)) == 0:
            return False

        # Changes the start time for all matching items in all three databases
        for i in f:
            i.start = start
        for i in o:
            i.start = start
        for i in p:
            i.start = start

        self.full.commit()
        self.playing.commit()
        self.onhold.commit()

    # Add 1 to the amount of times the video/song has been played
    def add_playing_times(self, item):
        f = self.full.query(Item).filter_by(link=item.link, name=item.name)
        o = self.onhold.query(Item).filter_by(link=item.link, name=item.name)
        p = self.playing.query(Item).filter_by(link=item.link, name=item.name)

        # If no item is found in playing or onhold there's a problem with your db
        assert len(list(o)) > 0 or len(list(p)) > 0, "No item found"

        # If item is not found in onhold it must be in playing
        if len(list(o)) == 0:
            o = p

        for i, ii in zip(f, o):
            if i.play_times is None:
                i.play_times = 1
                ii.play_times = 1
            else:
                i.play_times += 1
                ii.play_times += 1

        self.full.commit()
        self.playing.commit()
        self.onhold.commit()
