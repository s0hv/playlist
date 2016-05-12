# Custom-playlist

This was created in python 3.4.4 and it's an early version so it will change a lot. Chrome extensions (in crx form) go in the folder src/Extensions. I suggest you get adblock since ads might confuse the program

## Installation

Install the chrome native host by double clicking the install_host.bat in native messaging host folder. Run the program with the command `python playlist.py` or use the start.bat file. Playlists are created with `python addlink.py` 

## Requirements:

Python 3.4.4 or later

Selenium `pip install selenium`

requests `pip install requests`

sqlalchemy `pip install SQLAlchemy`

zmq `pip install pyzmq`

[chromedriver](https://sites.google.com/a/chromium.org/chromedriver/)

[chrome](https://www.google.com/chrome/browser/desktop/index.html)

system hotkey for keyboard hotkeys like next song/video `pip3 install system_hotkey`. This also requires [pywin32](https://sourceforge.net/projects/pywin32/files/pywin32/Build%20220/)

If you are having problems with the system hotkey try [commenting out](https://gyazo.com/d992536c001ef3f7d28fac9c1c04f7d3) these lines (starting from 95) from the system_hotkey.py file


## Optional things:

pillow `pip install pillow` this is for rainmeter cover art

[autoit](https://www.autoitscript.com/site/) if you want to change the volume of chrome instance with keyboard keys. The file also needs to be compiled but it's prety easy with autoit.

Volume changer also needs [NirCmd](http://www.nirsoft.net/utils/nircmd.html)
