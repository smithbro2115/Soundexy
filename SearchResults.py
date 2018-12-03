from tinytag import TinyTag
import soundfile as sf
import os


class Local:
    def __init__(self):
        self.title = ''
        self.duration = None
        self.description = ''
        self.id = None
        self.author = ''
        self.library = 'Local'
        self.channels = 0
        self.file_type = ''
        self.path = ''
        self.bitrate = None
        self.keywords = []
        self.album_image = None

    def populate(self, path, identification_number):
        print(path)
        self.id = identification_number
        self.path = path
        self.title = os.path.basename(path)
        self.file_type = os.path.splitext(path)[1]
        self.library = self.get_library(path)
        self.keywords = self.get_words()
        if self.file_type.lower() == '.wav':
            try:
                f = sf.SoundFile(path)
                self.duration = (len(f) / f.samplerate)*1000
                print(self.duration)
                self.channels = f.channels
            except RuntimeError:
                print('Unrecognized file type')
        else:
            try:
                f = TinyTag.get(path, image=True)
            except Exception as e:
                print(e)
            else:
                self.album_image = f.get_image()
                print(self.album_image)
                self.description = f.disc_total
                self.bitrate = f.bitrate
                if f.duration is not None:
                    self.duration = round(f.duration*1000)
                else:
                    self.duration = 1
                self.channels = f.channels

    def get_library(self, path):
        if 'Digital Juice' in path:
            return 'Digital Juice'
        elif 'SoundDogs' in path:
            return 'Sound Dogs Local'
        elif 'ProSound' in path:
            return 'Pro Sound Local'
        elif 'Adobe' in path:
            return 'Adobe'
        else:
            return 'Local'

    def get_words(self):
        path_list = list(self.path)
        new_path = []
        characters_to_replace = ['-', '_', '/', '\\', ',']
        characters_to_delete = ['.']
        for i, c in enumerate(path_list):
            if c in characters_to_delete:
                pass
            elif c in characters_to_replace:
                new_path.append(' ')
            elif c.isupper():
                try:
                    previous_c = path_list[i-1]
                    next_c = path_list[i-1]
                except IndexError:
                    pass
                else:
                    if previous_c.lower() and next_c.lower():
                        new_path.append(' ' + c)
            else:
                new_path.append(c)
        new_path_str = ''.join(new_path)
        words = new_path_str.lower().split()
        words.append(self.path)
        return words

    def search(self, keywords, excluded_words=None):
        for keyword in keywords:
            if keyword.lower() in self.keywords:
                if excluded_words is not None:
                    if keyword.lower() in excluded_words:
                        return False
                return True
        return False


class Free:
    def __init__(self):
        self.title = ''
        self.preview = ''
        self.duration = None
        self.description = ''
        self.id = None
        self.author = ''
        self.link = ''
        self.library = ''
        self.file_type = ''

    def set_title(self, title):
        index = title.rfind('.')
        self.file_type = title[index:]
        self.title = title[:index]


class Paid:
    def __init__(self, keywords):
        print('test paid ' + str(keywords))
