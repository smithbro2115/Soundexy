import MetaData
from PyQt5.QtCore import pyqtSignal, QObject
import os
import Downloader


class Local:
    def __init__(self):
        self.signals = LocalSigs()
        self.title = ''
        self.name = ''
        self.duration = 0
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
        self.sample_rate = 48000
        self.meta_file = None

    def populate(self, path, identification_number):
        self.id = identification_number
        self.path = path
        self.library = self.get_library(path)
        self.keywords = self.get_words()
        try:
            self.meta_file = MetaData.get_meta_file(self.path)
        except AttributeError:
            return False
        else:
            self.file_type = self.meta_file['file type']
            self.sample_rate = self.meta_file['sample rate']
            self.duration = self.meta_file['duration']
            self.channels = self.meta_file['channels']
            return True

    def repopulate(self):
        self.populate(self.path, self.id)

    @staticmethod
    def get_library(path):
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

    def set_tag(self, tag, value):
        self.meta_file.set_tag(tag, value)
        self.repopulate()
        print(self.signals)
        self.signals.meta_changed.emit(self)

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

    def get_dict_of_all_attributes(self):
        return {'Filename': self.meta_file.filename, 'Title': self.title,
                'Duration': str(self.duration) + ' ms', 'Description': self.description, 'ID': self.id,
                'Author': self.author, 'Library': self.library, 'Channels': self.channels,
                'File Type': self.file_type, 'File Path': self.path, 'Bit Rate': self.bitrate,
                'Keywords': self.keywords, 'Sample Rate': self.sample_rate}


class LocalSigs(QObject):
    failed_to_load_meta = pyqtSignal(str)
    meta_changed = pyqtSignal(Local)


class RemoteSigs(QObject):
    downloaded_some = pyqtSignal(int)
    download_done = pyqtSignal(str)
    ready_for_preview = pyqtSignal(str)
    preview_done = pyqtSignal(str)
    preview_already_exists = pyqtSignal(str)
    download_started = pyqtSignal()
    download_already_exists = pyqtSignal(str)
    download_deleted = pyqtSignal()


class Free:
    def __init__(self):
        self.title = ''
        self.preview = ''
        self.duration = 0
        self.description = ''
        self.id = None
        self.author = ''
        self.link = ''
        self.library = ''
        self.file_type = ''
        self.signals = RemoteSigs()
        self.tags = self.meta_file()
        self.download_path = 'downloads'
        self.downloader = None
        self._file_name = ''

    def set_title(self, title):
        index = title.find('.')
        if index >= 0:
            self.file_type = title[index:]
            self.title = title[:index]
        else:
            self.title = title

    def meta_file(self):
        return {'file name': self.title, 'title': self.title, 'duration': self.duration, 'description': self.description, 'id': self.id,
                'author': self.author, 'library': self.library, 'preview Link': self.preview,
                'file type': self.file_type, 'download link': self.link}

    def download(self, threadpool):
        self.downloader = Downloader.AuthDownloader(self.meta_file()['download link'], 'smithbro', 'Ferrari578')
        self.downloader.download_path = self.download_path
        self.signals.download_started.emit()
        self.downloader.signals.downloaded_some.connect(lambda x: self.signals.downloaded_some.emit(x))
        self.downloader.signals.already_exists.connect(self._download_done)
        self.downloader.signals.download_done.connect(self._download_done)
        threadpool.start(self.downloader)

    def _download_done(self, filename):
        print(filename)
        self._file_name = filename
        self.signals.download_done.emit(filename)

    def cancel_download(self):
        self.downloader.cancel()
        self.signals.download_deleted.emit()

    def delete_download(self):
        os.remove(self._file_name)
        self.signals.download_deleted.emit()

    def download_preview(self, threadpool, current):
        if threadpool.activeThreadCount() > 0:
            current.cancel()
        downloader = Downloader.PreviewDownloader(self.meta_file()['preview Link'], self.meta_file()['id'])
        downloader.signals.downloaded.connect(lambda x: self.signals.ready_for_preview.emit(x))
        downloader.signals.already_exists.connect(lambda x: self.signals.preview_already_exists.emit(x))
        downloader.signals.download_done.connect(lambda x: self.signals.preview_done.emit(x))
        threadpool.start(downloader)
        return downloader


class Paid:
    def __init__(self, keywords):
        print('test paid ' + str(keywords))
