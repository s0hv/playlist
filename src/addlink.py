#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src import database as db
from src.database import Item
import tkinter as tk
from tkinter import GROOVE, Button, Listbox, Label, SINGLE, Entry, Frame, messagebox, Text
from tkinter.filedialog import askopenfilename
from src import config as cfg

config = cfg.Config()
currently_set = None
database = db.DatabaseHandler()
full, playing = None, None


def set_database(path, create=False):
    global full, playing, currently_set
    if path != currently_set:
        value = database.set_database(path, create)
        if value is False:
            messagebox.showerror('File error', "Could not create the file")
            return False
        full = database.full
        playing = database.playing
        currently_set = path


def greytext(entry):
    entry.delete(0, 'end')
    entry.config(fg='black')
    entry.unbind('<Button-1>')


class MainApp(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        # Container where the different Frames stack
        container = Frame(self)
        container.pack(side='top', fill='both', expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (Main, ReadFromFile, AddManually):
            page_name = F.__name__
            frame = F(container, self)
            self.frames[page_name] = frame

            frame.grid(row=0, column=0, sticky='nsew')

        self.show_frame('Main')

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

    def quit(self):
        self.destroy()

    @staticmethod
    def add_item(link, name):
        item = Item(link=link, name=name)
        item2 = Item(link=link, name=name)
        full.add(item)
        full.commit()
        playing.add(item2)
        playing.commit()


class ReadFromFile(Frame):

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        self.link_first = True
        self.items = []

        self.place(relx=0.0, rely=0.0, relheight=0.62, relwidth=0.72)
        self.configure(relief=GROOVE)
        self.configure(borderwidth="2")

        label_top = Label(self)
        label_top.place(relx=0.42, rely=0.03, height=21, width=105)
        label_top.configure(text="Select a file to read")

        self.file_select = Button(self, command=self.fopen)
        self.file_select.place(relx=0.43, rely=0.14, height=34, width=97)
        self.file_select.configure(text="Select file")

        self.back = Button(self, command=lambda: controller.show_frame('Main'))
        self.back.place(relx=0.8, rely=0.87, height=34, width=97)
        self.back.configure(text="Go back")

        self.delimeter = Entry(self)
        self.delimeter.place(relx=0.02, rely=0.11, relheight=0.06, relwidth=0.21)
        self.delimeter.insert(0, ' -<>- ')

        label_delim = Label(self)
        label_delim.place(relx=0.02, rely=0.03, height=21, width=57)
        label_delim.configure(text="Delimeter")

        self.switch_label = Label(self)
        self.switch_label.place(relx=0.73, rely=0.31, height=21, width=38)
        self.switch_label.configure(text="Link")

        self.switch_label2 = Label(self)
        self.switch_label2.place(relx=0.9, rely=0.31, height=21, width=38)
        self.switch_label2.configure(text="Name")

        self.change_order = Button(self, command=self.switch_order)
        self.change_order.place(relx=0.82, rely=0.31, height=24, width=32)
        self.change_order.configure(text="<->")

        name_or_link = Label(self)
        name_or_link.place(relx=0.75, rely=0.19, height=21, width=97)
        name_or_link.configure(text="Name or link first")

        self.items_text = Text(self)
        self.items_text.place(relx=0.02, rely=0.5, relheight=0.46, relwidth=0.76)
        self.items_text.configure(wrap=tk.WORD)

        label_items = Label(self)
        label_items.place(relx=0.35, rely=0.42, height=21, width=35)
        label_items.configure(text="Items")

        self.commit_btn = Button(self, command=self.commit)
        self.commit_btn.place(relx=0.83, rely=0.64, height=34, width=67)
        self.commit_btn.configure(text="Commit")

        self.Label12 = Label(self)
        self.Label12.place(relx=0.02, rely=0.19, height=21, width=88)
        self.Label12.configure(text="Link formatting (optional)")

        self.link_part1 = Entry(self)
        self.link_part1.place(relx=0.02, rely=0.28, relheight=0.06, relwidth=0.37)
        self.link_part1.insert(0, "https://www.youtube.com/watch?v=")

        self.link_part2 = Entry(self, fg='grey')
        self.link_part2.place(relx=0.02, rely=0.36, relheight=0.06, relwidth=0.37)
        self.link_part2.insert(0, "End of the link here")
        self.link_part2.bind('<Button-1>', lambda event: greytext(self.link_part2))

    def fopen(self):
        self.filename = askopenfilename()
        if self.filename == '':
            return
        self.items.clear()
        self.items_text.delete(1.0, 'end')
        with open(self.filename, encoding='utf-8-sig') as f:
            lines = f.read().splitlines()

        delim = self.delimeter.get()
        for line in lines:
            try:
                link, name = line.split(delim, 1)
                if not self.link_first:
                    name, link = link, name
                if '{DELETED} ' in name[:13]:
                    continue
                s, e = self.get_link_formatting()
                link = s + link + e
                self.items += [(link, name)]
                self.items_text.insert('end', ("name: " + name + "\nlink: " + link + '\n\n'))
            except ValueError:
                print("Something went wrong: ", line)

    def get_link_formatting(self):
        link1, link2 = self.link_part1, self.link_part2
        start = ''
        end = ''
        if link1.cget('fg') != 'grey':
            start = link1.get()
        if link2.cget('fg') != 'grey':
            end = link2.get()
        return start, end

    def switch_order(self):
        s1, s2 = self.switch_label, self.switch_label2
        text1, text2 = s1.cget('text'), s2.cget('text')
        s1.configure(text=text2)
        s2.configure(text=text1)
        self.link_first = not self.link_first

    def commit(self):
        amount = len(self.items)
        failed = 0
        for item in self.items:
            try:
                self.controller.add_item(item[0], item[1])
                print('Added ' + item[1] + ', ' + item[0])
            except:
                failed += 0
        print(str(amount - failed) + '/' + str(amount) + ' Items added')
        response = input("Do you want to empty the contents of the file used (Y/N)")
        if response.lower() == "y" or "yes":
            open(self.filename, 'w').close()


class AddManually(Frame):

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller

        self.place(relx=0.0, rely=0.0, relheight=0.62, relwidth=0.72)
        self.configure(relief=GROOVE)
        self.configure(borderwidth="2")
        self.configure(relief=GROOVE)
        self.configure(width=125)

        self.label_top = Label(self)
        self.label_top.place(relx=0.4, rely=0.03, height=21, width=112)
        self.label_top.configure(text="Add items manually")

        self.name = Entry(self, fg='grey')
        self.name.place(relx=0.05, rely=0.31, relheight=0.08, relwidth=0.29)
        self.name.insert(0, "Input name here")
        self.name.bind('<Button-1>', lambda event: greytext(self.name))

        self.link = Entry(self, fg='grey')
        self.link.place(relx=0.65, rely=0.31, relheight=0.08, relwidth=0.29)
        self.link.insert(0, "Input link here")
        self.link.bind('<Button-1>', lambda event: greytext(self.link))

        self.add_btn = Button(self, command=self.send_data)
        self.add_btn.place(relx=0.42, rely=0.44, height=34, width=100)
        self.add_btn.configure(text="Add item")

        self.back = Button(self, command=lambda: controller.show_frame('Main'))
        self.back.place(relx=0.42, rely=0.64, height=34, width=100)
        self.back.configure(text="Go back")

        name_label = Label(self)
        name_label.place(relx=0.05, rely=0.22, height=21, width=38)
        name_label.configure(text="Name")

        link_label = Label(self)
        link_label.place(relx=0.65, rely=0.22, height=21, width=28)
        link_label.configure(text="Link")

    def send_data(self):
        if self.link.cget('fg') == 'grey' or self.name.cget('fg') == 'grey':
            return
        link = self.link.get()
        if link.strip() != '':
            name = self.name.get()
            self.controller.add_item(link, name)
            print("Item added")


class Main(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        self.db_set = False

        self.configure(relief=GROOVE)
        self.configure(borderwidth="2")

        # Manual link adding
        self.manual_btn = Button(self)
        self.manual_btn.place(relx=0.07, rely=0.81, height=45, width=130)
        self.manual_btn.configure(activebackground="#d9d9d9")
        self.manual_btn.configure(highlightbackground="#d9d9d9")
        self.manual_btn.configure(pady="0")
        self.manual_btn.configure(text="Add manually")
        self.manual_btn.configure(width=130)

        self.file_btn = Button(self)
        self.file_btn.place(relx=0.67, rely=0.81, height=45, width=150)
        self.file_btn.configure(activebackground="#d9d9d9")
        self.file_btn.configure(highlightbackground="#d9d9d9")
        self.file_btn.configure(pady="0")
        self.file_btn.configure(text="Add from file")

        self.label = Label(self)
        self.label.place(relx=0.08, rely=0.0, height=61, width=484)
        self.label.configure(text="Create new playlists and add content to them")
        self.label.configure(width=485)

        self.listbox = Listbox(self)
        self.listbox.place(relx=0.38, rely=0.22, relheight=0.31, relwidth=0.17)
        self.listbox.configure(background="white")
        self.listbox.configure(disabledforeground="#a3a3a3")
        self.listbox.configure(foreground="#000000")
        self.listbox.configure(selectmode=SINGLE)
        self.listbox.configure(width=105)
        for name, value in config.configparser.items('Playlists'):
            if os.path.isdir(value):
                self.listbox.insert('end', name)
            else:
                config.remove_value('Playlists', name)
        self.listbox.bind('<<ListboxSelect>>', self.onselect)

        self.label_name = Label(self)
        self.label_name.place(relx=0.7, rely=0.22, height=31, width=84)
        self.label_name.configure(foreground="#000000")
        self.label_name.configure(text="Name")
        self.label_name.configure(width=85)

        self.entry = Entry(self)
        self.entry.place(relx=0.63, rely=0.31, relheight=0.08, relwidth=0.29)
        self.entry.configure(background="white")
        self.entry.configure(foreground="#000000")
        self.entry.configure(insertbackground="black")
        self.entry.configure(takefocus="0")
        self.entry.configure(width=175)

        self.change_name = Button(self)
        self.change_name.place(relx=0.7, rely=0.42, height=34, width=97)
        self.change_name.configure(activebackground="#d9d9d9")
        self.change_name.configure(highlightbackground="#d9d9d9")
        self.change_name.configure(highlightcolor="black")
        self.change_name.configure(pady="0")
        self.change_name.configure(text="Rename")
        self.change_name.configure(width=100)

        self.new_playlist = Button(self, command=self.new_database)
        self.new_playlist.place(relx=0.08, rely=0.28, height=54, width=107)
        self.new_playlist.configure(activebackground="#d9d9d9")
        self.new_playlist.configure(highlightbackground="#d9d9d9")
        self.new_playlist.configure(highlightcolor="black")
        self.new_playlist.configure(pady="0")
        self.new_playlist.configure(text="Create new playlist")
        self.new_playlist.configure(width=105)

        self.db_name = Entry(self)
        self.db_name.place(relx=0.07, rely=0.44, relheight=0.08, relwidth=0.22)
        self.db_name.configure(fg='grey')
        self.db_name.configure(width=135)
        self.db_name.insert(0, "Input database name here")
        self.db_name.bind('<Button-1>', lambda event: greytext(self.db_name))

    def onselect(self, event):
        w = event.widget
        index = int(w.curselection()[0])
        value = w.get(index)
        set_database(config.configparser.get('Playlists', value))
        if not database.check_integrity():
            messagebox.showwarning('Integrity check failed', 'You might be missing some entries in your list')
        if not self.db_set:
            self.manual_btn.configure(command=lambda: self.controller.show_frame('AddManually'))
            self.file_btn.configure(command=lambda: self.controller.show_frame('ReadFromFile'))
            self.db_set = True

    def new_database(self):
        name = self.db_name.get()
        names = config.configparser.options('Playlists')
        print(name, names)
        if name.strip() == '' or self.db_name.cget('fg') == 'grey':
            messagebox.showerror('Invalid name', "Please input a valid name for the database")
            return
        if name in names:
            messagebox.showerror('Name already in use', "Please select another name")
            return
        path = '../playlists/%s/' % name
        if set_database(path, create=True) is False:
            return
        config.set_value('Playlists', name, path)
        self.listbox.insert('end', name)

if __name__ == '__main__':
    app = MainApp()
    app.resizable(width=False, height=False)
    app.geometry('600x360')
    app.mainloop()
