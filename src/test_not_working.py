import sys, os, codecs, time
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

from selenium.webdriver import Chrome
from database import DatabaseHandler, Item

from system_hotkey import SystemHotkey

working = False
done = False


def is_working():
    global working, done
    working = True
    done = True


def not_working():
    global working, done
    working = False
    done = True

hk = SystemHotkey()
hk.register(('control', 'numpad3'), callback=lambda e: is_working())
hk.register(('control', 'numpad1'), callback=lambda e: not_working())

driver = Chrome()

db = DatabaseHandler()
db.set_database(None, name='default')
db.connect_not_working()
q = db.not_working.query(Item)

for item in q:
    driver.get(item.link)
    while not done:
        time.sleep(0.1)

    if working:
        db.not_working.delete(item)
        db.not_working.commit()

    done = False

driver.quit()

db.delete_items(db.not_working.query(Item))
