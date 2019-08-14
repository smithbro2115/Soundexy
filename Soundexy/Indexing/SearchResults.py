from Soundexy.MetaData import MetaData
from Soundexy.Functionality.useful_utils import get_app_data_folder
from Soundexy.Webscraping.Authorization.Credentials import get_credentials, delete_saved_credentials, \
    get_saved_credentials
import os
from Soundexy.Webscraping.Downloading import Downloader
from Soundexy.Webscraping.Buying.Buyer import is_this_sound_bought_from_sound_dogs
from abc import abstractmethod
from Soundexy.Webscraping.Buying.WebBrowser import open_page
from Soundexy.Webscraping.Buying.Buyer import SoundDogsBuyer


class Result:
    def __init__(self):
        self._meta_file = None
        self.meta_file = None
        self.title = ''
        self.name = ''
        self.duration = 0
        self.description = ''
        self.id = None
        self.author = ''
        self.library = ''
        self.channels = 0
        self.file_type = ''
        self.path = ''
        self.bitrate = None
        self.keywords = []
        self.album_image = None
        self.sample_rate = 48000
        self.index_path = ''
        self.index_file_name = ''

    @property
    def precise_duration(self):
        return self.duration

    @property
    def meta_file(self):
        return self._meta_file

    @meta_file.setter
    def meta_file(self, value):
        self._meta_file = value

    def __eq__(self, other):
        try:
            if self.id == other.id:
                return True
        except AttributeError:
            pass
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def available_locally(self):
        return True

    def get_dict_of_all_attributes(self):
        return {'Filename': self._meta_file.filename, 'Title': self.title,
                'Duration': str(self.duration) + ' ms', 'Description': self.description, 'ID': self.id,
                'Author': self.author, 'Library': self.library, 'Channels': self.channels,
                'File Type': self.file_type, 'File Path': self.path, 'Bit Rate': self.bitrate,
                'Keywords': self.keywords, 'Sample Rate': self.sample_rate, 'Available Locally': self.available_locally}


class Local(Result):
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
        from Soundexy.Indexing.LocalFileHandler import IndexFile
        index = IndexFile(self.index_file_name, self.index_path)
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

    def search(self, search_words, excluded_words=None):
        for word in search_words:
            for keyword in self.keywords:
                if word.lower() in keyword:
                    if excluded_words is not None:
                        if keyword.lower() in excluded_words:
                            return False
                    return True
        return False


class Remote(Result):
    def __init__(self):
        super(Remote, self).__init__()
        self.download_path = f"{get_app_data_folder('downloads')}"
        self.index_path = 'obj'
        self.preview = ''
        self.link = ''
        self.index_file_name = 'downloaded_index'
        self.downloader = None
        self.downloading = False
        self.downloaded = False
        self.original_id = 0

    @property
    def preview_link(self):
        return self.meta_file['preview Link']

    def check_if_already_downloaded(self):
        from Soundexy.Indexing.LocalFileHandler import IndexFile
        for result in IndexFile(self.index_file_name, self.index_path).index:
            if self == result:
                return result

    @property
    def available_locally(self):
        return self.downloaded

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

    @property
    def meta_file(self):
        return {'file name': self.title, 'title': self.title, 'duration': self.duration,
                'description': self.description, 'id': self.id,
                'author': self.author, 'library': self.library, 'preview Link': self.preview,
                'sample rate': self.sample_rate,
                'file type': self.file_type, 'download link': self.link, 'available locally': self.downloaded}

    @meta_file.setter
    def meta_file(self, value):
        self._meta_file = value

    def get_downloaded_index(self):
        from Soundexy.Indexing.LocalFileHandler import IndexFile
        return IndexFile(self.index_file_name, self.index_path)

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
        downloader = self.preview_downloader(self.preview_link, self.id)
        downloader.signals.downloaded.connect(lambda x: downloaded_some_f(x))
        downloader.signals.already_exists.connect(lambda x: self._preview_download_done(x, downloaded_already_f))
        downloader.signals.download_done.connect(lambda x: self._preview_download_done(x, done_f))
        threadpool.start(downloader)
        return downloader

    @property
    def preview_downloader(self):
        return Downloader.PreviewDownloader

    def get_downloader(self):
        return Downloader.Downloader

    def download(self, threadpool, download_started_f, downloaded_some_f, download_done_f, cancel_f, error_f):
        self.downloader = self.construct_auth_session()
        if not self.downloader:
            return None
        self.downloader.download_path = self.download_path
        download_started_f(self.id)
        self.connect_downloader_signals(downloaded_some_f, download_done_f, cancel_f, error_f)
        threadpool.start(self.downloader)
        self.downloading = True

    def connect_downloader_signals(self, d_some_f, d_done_f, d_cancel_f, d_error_f):
        self.downloader.signals.error.connect(lambda x: self.download_error(x, d_cancel_f, d_error_f))
        self.downloader.signals.wrong_credentials.connect(lambda x: self.download_wrong_credentials(x, d_cancel_f,
                                                                                                    d_error_f))
        self.downloader.signals.downloaded_some.connect(lambda x: d_some_f(x, self.id))
        self.downloader.signals.already_exists.connect(lambda x: self._download_done(x, d_done_f))
        self.downloader.signals.download_done.connect(lambda x: self._download_done(x, d_done_f))

    def download_error(self, msg, c_function, e_function):
        e_function(msg)
        self.cancel_download(c_function)

    def download_wrong_credentials(self, msg, c_function, e_function):
        self.wrong_credentials(msg, e_function)
        self.cancel_download(c_function)

    def wrong_credentials(self, msg, e_function):
        e_function(msg)
        delete_saved_credentials(self.library)

    def construct_auth_session(self):
        outcome = get_credentials(self.library)
        if outcome[1]:
            return self.get_downloader()(self, outcome[0])
        return None


class FreesoundResult(Remote):
    @property
    def site_name(self):
        return 'Freesound'

    def get_downloader(self):
        return Downloader.FreesoundDownloader


class Paid(Remote):
    def __init__(self):
        super(Paid, self).__init__()
        self.bought = False
        self.buying = False
        self.price = 0

    @property
    def meta_file(self):
        m = super(Paid, self).meta_file
        m['bought'] = self.bought
        m['price'] = self.price
        return m

    @meta_file.setter
    def meta_file(self, value):
        self._meta_file = value

    @property
    def site_name(self):
        return ''

    def buy(self, thread_pool, e_function):
        pass

    def check_if_bought(self):
        pass


class ProSoundResult(Paid):
    @property
    def preview_link(self):
        auth = Downloader.pro_sound_get_preview_auth(self.original_id)
        return f"{self.meta_file['preview Link']}?{auth}"

    @property
    def site_name(self):
        return 'Pro Sound'

    def get_downloader(self):
        return Downloader.ProSoundDownloader


class SoundDogsResult(Paid):
    def __init__(self):
        super(SoundDogsResult, self).__init__()
        self.got_true_duration = False
        self._precise_duration = 0

    def buy(self, thread_pool, e_function):
        buyer = SoundDogsBuyer(self.original_id, *get_credentials(self.library)[0])
        buyer.signals.error.connect(lambda x: self.wrong_credentials(x, e_function))
        buyer.signals.finished.connect(lambda: open_page('https://www.sounddogs.com/basket/view'))
        thread_pool.start(buyer)

    @property
    def precise_duration(self):
        if not self.got_true_duration:
            self._precise_duration = self.get_true_duration()
        return self._precise_duration

    @precise_duration.setter
    def precise_duration(self, value):
        self._precise_duration = value

    @property
    def site_name(self):
        return 'Sound Dogs'

    def get_true_duration(self):
        self.got_true_duration = True
        return Downloader.get_sound_dogs_true_duration(self.original_id)

    def get_downloader(self):
        return Downloader.SoundDogsDownloader

    def check_if_bought(self):
        try:
            username, password = get_saved_credentials(self.library)
            self.bought = is_this_sound_bought_from_sound_dogs(self.original_id, username, password)
            return self.bought
        except KeyError:
            return False
