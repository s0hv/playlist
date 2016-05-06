import configparser, os


class Config(object):
    def __init__(self):
        self.configparser = configparser.ConfigParser()
        self.configparser.optionxform = str
        configdir = os.path.join(__file__, '..', 'config.ini')
        self.configparser.read(configdir)

    def reset(self):
        self.configparser['Playlists'] = {'default': 'playlists/Default/'}
        self.configparser['List Options'] = {'playing_size': 0.3,
                                  'onhold_size': 0.7}
        self.configparser['Hotkeys'] = {'next': 'numpad3'}

        with open('config.ini', 'w') as f:
            self.configparser.write(f)

    if not os.path.isfile(os.path.join(__file__, '..', 'config.ini')):
        print(__file__)
        reset()

    def write_config(self):
        with open('config.ini', 'w')as f:
            self.configparser.write(f)

    def set_value(self, section, option, value):
        try:
            self.configparser.set(section, option, value)
            self.write_config()
        except configparser.NoSectionError:
            print("Error")
            return False

    def remove_value(self, section, option):
        try:
            self.configparser.remove_option(section, option)
            self.write_config()
        except configparser.NoSectionError:
            print("Could not delete option")
            return False
