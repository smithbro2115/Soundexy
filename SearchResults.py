import MetaData
from PyQt5.QtCore import pyqtSignal, QObject
import sys
import os
import Downloader
from abc import abstractmethod


class Local:
    def __init__(self):
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
        self.index_file_name = 'local_index'
        self.available_locally = True

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
        from LocalFileHandler import IndexFile
        index = IndexFile(self.index_file_name)
        index.changed_meta_data(self)

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
                'Keywords': self.keywords, 'Sample Rate': self.sample_rate, 'Available Locally': self.available_locally}


class RemoteSigs(QObject):
    downloaded_some = pyqtSignal(int)
    download_done = pyqtSignal(str)
    ready_for_preview = pyqtSignal(str)
    preview_done = pyqtSignal(str)
    preview_already_exists = pyqtSignal(str)
    download_started = pyqtSignal()
    download_already_exists = pyqtSignal(str)
    download_deleted = pyqtSignal()


class Remote:
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
        self.download_path = 'downloads'
        self.index_file_name = 'downloaded_index'
        self.downloader = None
        self.downloading = False
        self.downloaded = False
        self.path = ''
        self.sample_rate = 44100

    def __eq__(self, other):
        try:
            return self.meta_file()['id'] == other.meta_file()['id']
        except (AttributeError, KeyError):
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def check_if_already_downloaded(self):
        from LocalFileHandler import IndexFile
        for result in IndexFile(self.index_file_name).index:
            if self == result:
                return result

    @property
    @abstractmethod
    def site_name(self):
        return ''

    def set_title(self, title):
        index = title.find('.')
        if index >= 0:
            self.file_type = title[index:]
            self.title = title[:index]
        else:
            self.title = title

    def meta_file(self):
        return {'file name': self.title, 'title': self.title, 'duration': self.duration, 'description': self.description, 'id': self.id,
                'author': self.author, 'library': self.library, 'preview Link': self.preview, 'sample rate': self.sample_rate,
                'file type': self.file_type, 'download link': self.link, 'available locally': self.downloaded}

    @abstractmethod
    def download(self, threadpool, download_started_f, downloaded_some_f, download_done_f):
        pass

    def get_downloaded_index(self):
        from LocalFileHandler import IndexFile
        return IndexFile(self.index_file_name)

    def _download_done(self, filename, function):
        self.path = filename
        self.downloading = False
        self.downloader = None
        self.downloaded = True
        self.sample_rate = self._get_sample_rate()
        self.add_to_index()
        function(self)

    def _get_sample_rate(self):
        meta = MetaData.get_meta_file(self.path)
        return meta['sample rate']

    def _preview_download_done(self, filename, function):
        self._file_name = filename
        function(filename)

    def cancel_download(self, function):
        self.downloading = False
        self.downloader.cancel()
        self.downloader = None
        function()

    def delete_download(self, function):
        self.downloaded = False
        function()
        self.delete_from_index()
        os.remove(self.path)

    def delete_from_index(self):
        index = self.get_downloaded_index()
        index.delete_from_index(self)

    def add_to_index(self):
        index = self.get_downloaded_index()
        index.add_result_to_index(self)
        index.save()

    def download_preview(self, threadpool, current, downloaded_some_f, done_f, downloaded_already_f):
        if threadpool.activeThreadCount() > 0:
            current.cancel()
        downloader = Downloader.PreviewDownloader(self.meta_file()['preview Link'], self.meta_file()['id'])
        downloader.signals.downloaded.connect(lambda x: downloaded_some_f(x))
        downloader.signals.already_exists.connect(lambda x: self._preview_download_done(x, downloaded_already_f))
        downloader.signals.download_done.connect(lambda x: self._preview_download_done(x, done_f))
        threadpool.start(downloader)
        return downloader

    def get_downloader(self):
        return Downloader.Downloader


class Free(Remote):
    @property
    @abstractmethod
    def site_name(self):
        return ''

    def download(self, threadpool, download_started_f, downloaded_some_f, download_done_f):
        self.downloader = self.get_downloader()(self.meta_file()['download link'])
        self.downloader.download_path = self.download_path
        download_started_f()
        self.downloader.signals.downloaded_some.connect(lambda x: downloaded_some_f(x, self.id))
        self.downloader.signals.already_exists.connect(lambda x: self._download_done(x, download_done_f))
        self.downloader.signals.download_done.connect(lambda x: self._download_done(x, download_done_f))
        threadpool.start(self.downloader)
        self.downloading = True


class FreesoundResult(Free):
    @property
    def site_name(self):
        return 'Freesound'

    def get_downloader(self):
        return Downloader.FreesoundDownloader


class Paid(Remote):
    def __init__(self):
        super(Paid, self).__init__()

    def download(self, threadpool, download_started_f, downloaded_some_f, download_done_f):
        pass
