from Soundexy.MetaData import MetaData
from Soundexy.Functionality.useful_utils import get_app_data_folder, construct_in_different_thread, \
    check_if_sound_is_bought_in_separate_thread, DeleteThread
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
        self.meta_file = {}
        self.index_path = ''
        self.index_file_name = ''

    def __getattr__(self, item):
        try:
            return self.meta_file[item]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")

    @property
    def precise_duration(self):
        return self.duration

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


class Local(Result):
    def __init__(self, hit):
        super(Local, self).__init__()
        self._meta_file = None
        self.hit = hit
        self.id = f"local_{hit.docnum}"
        self.docnum = hit.docnum
        self.library = self.get_library(self.meta_file['path'])
        self.sample_rate = self.meta_file['sample_rate']
        self.duration = self.meta_file['duration']
        self.meta_file['available_locally'] = True

    @property
    def meta_file(self):
        return self.hit.fields()

    @meta_file.setter
    def meta_file(self, value):
        self._meta_file = value

    def populate(self, path, identification_number):
        self.id = identification_number
        self.meta_file['path'] = path
        self.meta_file['library'] = self.get_library(path)
        self.meta_file['keywords'] = self.get_words()
        self.meta_file['available_locally'] = True
        # try:
        #     # self.meta_file = MetaData.get_meta_file(self.path)
        # except AttributeError:
        #     return False
        # else:
        #     self.file_type = self.meta_file['file type']
        #     self.sample_rate = self.meta_file['sample rate']
        #     self.duration = self.meta_file['duration']
        #     self.channels = self.meta_file['channels']
        #     return True

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


class Remote(Result):
    def __init__(self):
        super(Remote, self).__init__()
        self.download_path = f"{get_app_data_folder('downloads')}"
        self.meta_file['available_locally'] = False
        self.index_path = 'index'
        self.index_file_name = 'downloaded'
        self.downloader = None
        self.downloading = False
        self.meta_file['downloaded'] = False

    def check_if_already_downloaded(self):
        from Soundexy.Indexing.LocalFileHandler import IndexSearch
        search = IndexSearch(f"id:{self.id}", index_name=self.index_file_name)
        results = search.search()
        if len(results) > 0:
            self.meta_file = results[0].fields()
            return self

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
            self.meta_file['file_type'] = title[index:]
            self.meta_file['title'] = title[:index]
        else:
            self.meta_file['title'] = title

    def set_filename(self, filename):
        index = filename.find('.')
        if index >= 0:
            self.meta_file['file_type'] = filename[index:]
        self.meta_file['file_name'] = filename

    @staticmethod
    def try_to_set_variable_from_dict(dictionary, key):
        try:
            return dictionary[key]
        except KeyError:
            return None

    def get_downloaded_index(self):
        from Soundexy.Indexing.LocalFileHandler import IndexFile
        from Soundexy.Indexing.Indexing import RemoteSchema
        return IndexFile(self.index_file_name, schema=RemoteSchema)

    def _download_done(self, filename, function):
        self.meta_file['path'] = filename
        self.downloading = False
        self.downloader = None
        self.meta_file['downloaded'] = True
        self.meta_file['sample_rate'] = self._get_sample_rate()
        self.meta_file['available_locally'] = True
        self.meta_file.update(normalize_meta_dict(MetaData.get_meta_file(filename).meta))
        self.set_filename(os.path.basename(filename))
        self.add_to_index()
        function(self)

    def _get_sample_rate(self):
        # meta = MetaData.get_meta_file(self.path)
        # return meta['sample rate']
        return 48000

    def _preview_download_done(self, filename, function):
        self._file_name = filename
        function(filename)

    def cancel_download(self, function):
        self.downloading = False
        self.downloader.cancel()
        self.downloader = None
        function()

    def delete_download(self, function):
        thread = DeleteThread(self.meta_file['path'])
        del self.meta_file['path']
        self.meta_file['downloaded'] = False
        del self.meta_file['sample_rate']
        self.meta_file['available_locally'] = False
        function()
        self.delete_from_index()
        thread.start()

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
        self.buying = False
        self.meta_file['bought'] = False
        self.meta_file['price'] = 0

    @property
    def site_name(self):
        return ''

    def buy(self, thread_pool, e_function, c_function, s_function, f_function):
        open_page(f"https://download.prosoundeffects.com/#!details?id={self.original_id}")

    def check_if_bought(self):
        pass


class ProSoundResult(Paid):
    @property
    def preview_link(self):
        auth = Downloader.pro_sound_get_preview_auth(self.original_id)
        return f"{self.meta_file['preview_link']}?{auth}"

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

    def buy(self, thread_pool, e_function, c_function, s_function, f_function):
        check_if_sound_is_bought_in_separate_thread(self, lambda x: self.buy_confirmed(thread_pool,
                                                    e_function, c_function, s_function, f_function), thread_pool)

    def buy_confirmed(self, thread_pool, e_function, c_function, s_function, f_function):
        if not self.bought:
            self.buying = True
            s_function()
            credentials, accepted = get_credentials(self.library)
            if accepted:
                construct_in_different_thread(thread_pool, lambda x: self.buy_from_buyer(x, thread_pool, e_function,
                                              f_function), SoundDogsBuyer, self.original_id, *credentials)
            else:
                self.buying = False
                c_function()

    def buy_from_buyer(self, buyer, thread_pool, e_function, f_function):
        buyer.signals.error.connect(lambda x: self.wrong_credentials(x, e_function))
        buyer.signals.finished.connect(lambda: self._bought(f_function))
        thread_pool.start(buyer)

    def _bought(self, f_function):
        self.buying = False
        f_function()
        open_page('https://www.sounddogs.com/basket/view')

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
            self.meta_file['bought'] = is_this_sound_bought_from_sound_dogs(self.original_id, username, password)
            return self.bought
        except KeyError:
            return False


def normalize_meta_dict(meta_dict):
    new_dict = {}
    for key, value in meta_dict.items():
        if isinstance(value, list):
            new_dict[key.replace(" ", "_")] = value[0]
        else:
            new_dict[key.replace(" ", "_")] = value
    return new_dict
