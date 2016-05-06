#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy import Integer, Column, String, INTEGER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src import config as cfg
import random, math, os

Base = declarative_base()


class Item(Base):
    __tablename__ = "playlist"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    link = Column(String)
    start = Column(INTEGER, default=-1) # The length of the video in seconds. If 0 the program will automatically assign one when the video is played.


class DatabaseHandler(object):
    def __init__(self):
        if not os.path.isdir('../playlists'):
            os.mkdir('../playlists')

        self.full, self.playing, self.onhold, self.saved, self.deleted = None, None, None, None, None # All the different databases
        self.engine_full, self.engine_onhold, self.engine_playing = None, None, None                  # DB engines
        self.list_size = 0             # The size of the playlist
        self.not_working = None        # Another database
        self.wd = None                 # Working dir
        self.config = cfg.Config()     # The config handler

    # Set the active database
    def set_database(self, path, create=False, name=None):
        if name is not None:
            path = self.config.configparser.get('Playlists', name)
        self.wd = path
        print('%splaylist.db' % path)
        self.engine_full = create_engine('sqlite:///%splaylist.db' % path)  # , echo=True)
        self.engine_playing = create_engine('sqlite:///%splaylist_playing.db' % path)  # , echo=True)
        self.engine_onhold = create_engine('sqlite:///%splaylist_onhold.db' % path)  # , echo=True)

        Session = sessionmaker()
        Session2 = sessionmaker()
        Session3 = sessionmaker()

        if create:
            try:
                if not os.path.exists(path):
                    os.mkdir(path)
            except WindowsError:
                return False
            Base.metadata.create_all(self.engine_full)
            Base.metadata.create_all(self.engine_playing)
            Base.metadata.create_all(self.engine_onhold)

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
            id = item.id
            if id != idx:
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
        value = False

        if size <= self.list_size:
            value = True
        print(size, value)
        return value

    # Get a random item from the playlist
    @staticmethod
    def get_random(session):
        q = list(session.query(Item))
        return random.choice(q[0:math.ceil(len(q)*0.25)])

    # Create the item to an avaible id slot
    def create_item(self, name, link, session, start=-1):
        item = Item(link=link, name=name, start=start)
        i = self.get_id(session)
        if i is not None:
            item.id = i
        return item

    # Uses create_item to add an item to a database. Does not commit anything
    def add_item(self, session, item=None, name='', link=''):
        if item is None:
            if link == '':
                return False
            item = self.create_item(name, link, session)
        session.add(item)

    # Delete item by id
    @staticmethod
    def delete(engine, id):
        engine.execute('DELETE FROM playlist where ID = ' + str(id))

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
        item = Item(link=row.link, name=row.name, start=row.start)
        print(str(item.link), str(item.name))
        self.playing.delete(row)
        self.onhold.add(item)

        if self.check_size():
            items = list(self.onhold.query(Item))
            items = items[0:math.ceil(len(items) * 0.25)]
            row2 = random.choice(items)
            self.playing.add(Item(name=row2.name, link=row2.link, start=row2.start))
            self.onhold.delete(row2)

        self.playing.commit()
        self.onhold.commit()
        return row

    def add_not_working(self, item, delete=False):
        if self.wd is None:
            return

        if self.not_working is None:
            engine_notworking = create_engine('sqlite:///%splaylist_notworking.db' % self.wd)
            Session4 = sessionmaker()
            Base.metadata.create_all(engine_notworking)
            Session4.configure(bind=engine_notworking)
            self.not_working = Session4()

        link = item.link
        name = item.name
        itm = (Item(name=name, link=link, start=item.start))
        self.not_working.add(itm)
        self.not_working.commit()

        if delete and self.full is not None:
            self.onhold.delete(self.onhold.query(Item).filter_by(link=link, name=name).first())
            self.full.delete(self.full.query(Item).filter_by(link=link, name=name).first())
            self.full.commit()
            self.onhold.commit()
        return True

    # Do set delete_item to True when the playlist is not running
    # TODO delete_item
    def save_or_delete(self, item, save: bool, delete_item=False):
        item = Item(link=item.link, name=item.name, start=item.start)

        if save:
            if self.saved is None:
                engine_saved = create_engine('sqlite:///%splaylist_saved.db' % self.wd)
                Session5 = sessionmaker()
                Base.metadata.create_all(engine_saved)
                Session5.configure(bind=engine_saved)
                self.saved = Session5()
            self.saved.add(item)
            self.saved.commit()

        elif not save:
            if self.deleted is None:
                engine_deleted = create_engine('sqlite:///%splaylist_deleted.db' % self.wd)
                Session6 = sessionmaker()
                Base.metadata.create_all(engine_deleted)
                Session6.configure(bind=engine_deleted)
                self.deleted = Session6()
            self.deleted.add(item)
            self.deleted.commit()

    def delete_items(self):
        assert self.check_integrity() is True, "Playlist might be corrupted. Aborting"

        if self.full is None:
            return

        if self.deleted is None:
            engine_deleted = create_engine('sqlite:///%splaylist_deleted.db' % self.wd)
            Session6 = sessionmaker()
            Base.metadata.create_all(engine_deleted)
            Session6.configure(bind=engine_deleted)
            self.deleted = Session6()

        self.deleted.commit()
        items = self.deleted.query(Item)
        full_query = self.full.query(Item)
        onhold_query = self.onhold.query(Item)
        playing_query = self.playing.query(Item)

        for item in items:
            self.deleted.delete(item)
            self.full.delete(full_query.filter_by(link=item.link, name=item.name).first())
            if self.onhold.delete(onhold_query.filter_by(link=item.link, name=item.name).first()) is None:
                assert self.playing.delete(playing_query.filter_by(link=item.link,
                                                                   name=item.name).first()) is not None, "Item not found in playlists. Playlist might be corrupted"
        # TODO committing the changes

    @staticmethod
    # Just returns a new set of items
    def recreate_db(database):
        items = database.query(Item)
        new_items = []
        for item in items:
            name, link, start = item.name, item.link, item.start
            new_items += Item(name=name, link=link, start=start)
        return new_items

    # Copies a DB to another DB.
    def add_from_db(self, source, target, merge=False, duplicates=False):
        source
        # TODO Everything

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

    # TODO A function that resets the id values of the selected DB since the id grows all the time

    def update_start(self, item, start):
        f = self.full.query(Item).filter_by(link=item.link, name=item.name)
        o = self.onhold.query(Item).filter_by(link=item.link, name=item.name)
        p = self.playing.query(Item).filter_by(link=item.link, name=item.name)
        if len(list(o)) == 0 and len(list(p)) == 0:
            return False

        for i in f:
            i.start = start
        for i in o:
            i.start = start
        for i in p:
            i.start = start

        self.full.commit()
        self.playing.commit()
        self.onhold.commit()
