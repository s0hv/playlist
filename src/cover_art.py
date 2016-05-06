from PIL import Image
import configparser, os, subprocess, codecs, shutil, time


class SetCoverArt(object):

    def __init__(self, skin_folder, rainmeter):
        self.counter = 1
        if rainmeter is None or skin_folder is None:
            self.counter = None
            return
        assert os.path.exists(skin_folder) and os.path.exists(rainmeter)
        self.skin_folder = skin_folder
        self.resources = os.path.join(skin_folder, '@Resources')
        self.song_config = os.path.join(self.resources, 'Linear\\TrackInfo.inc')
        self.rainmeter = rainmeter
        self.config = configparser.ConfigParser()
        self.config.optionxform = str
        with open(self.song_config, 'rb') as f:
            encoded_text = f.read()
        bom = codecs.BOM_UTF16_LE
        assert encoded_text.startswith(bom)
        encoded_text = encoded_text[len(bom):]
        decoded_text = encoded_text.decode('utf-16le')
        self.config.read_string(decoded_text, self.song_config)

    def set_coverart(self, title: str, artist: str, image):
        if self.counter is None:
            return

        # Create image
        if image is not None:
            if self.counter == 1:
                image_name = 'cover1.png'
                self.counter = 2
            else:
                image_name = 'cover2.png'
                self.counter = 1

            destination = self.resources + '\\%s' % image_name
            opposite = 'cover%s.png' % self.counter

            image = Image.open(image)

            dimensions = max(image.size)
            if dimensions < 350:
                dimensions = 350
            size = (dimensions, dimensions)

            if image.size[0] != image.size[1]:

                if image.size[0] > image.size[1]:
                    x = image.size[0]
                    if x < dimensions:
                        image = image.resize((dimensions, int(size[0]/x*image.size[1])))
                else:
                    y = image.size[1]
                    if y < dimensions:
                        image = image.resize((int(size[0] / y * image.size[1]), dimensions))

                bg = Image.open(self.resources + '\\nocover.png')
                bg = bg.resize(size)

                image.thumbnail(size, Image.ANTIALIAS)
                bg.paste(image, (int((size[0] - image.size[0]) / 2), int((size[1] - image.size[1]) / 2)))

            elif image.size[0] == image.size[1]:
                bg = image
                bg.thumbnail(size, Image.ANTIALIAS)

            try:
                file = self.resources + '\\%s' % opposite
                os.remove(destination)
                shutil.copy(file, destination)
            except OSError:
                image_name = 'nocover.png'
            bg.save(destination, 'PNG')
        else:
            image_name = 'nocover.png'
            opposite = 'nocover.png'

        # Set config values
        self.config.set('Variables', 'Cover', '#@#%s' % opposite)
        self.config.set('Variables', 'Track', title)
        self.config.set('Variables', 'Artist', artist)
        self.config.set('Variables', '2Cover', '#@#%s' % image_name)
        self.write_config()

    def write_config(self):
        with open(self.song_config, 'wb') as f:
            f.write(codecs.BOM_UTF16_LE)
        with open(self.song_config, 'a', encoding='UTF-16LE') as f:
            self.config.write(f)
        subprocess.call([self.rainmeter, '!RefreshApp'])

    def quit(self):
        if self.counter is None:
            return

        c1 = self.resources + '\\cover1.png'
        c2 = self.resources + '\\cover2.png'
        try:
            os.remove(c1)
            os.remove(c2)
            shutil.copy(self.resources + '\\nocover.png', c1)
            shutil.copy(self.resources + '\\nocover.png', c2)
        except OSError:
            pass
