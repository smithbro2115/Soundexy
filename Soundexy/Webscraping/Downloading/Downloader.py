import requests
import re
import os
from Soundexy.Functionality.useful_utils import get_app_data_folder
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QRunnable
from Soundexy.Webscraping.Authorization import WebsiteAuth
from abc import abstractmethod


class NotOwnedError(Exception):
    pass


class DownloaderSigs(QObject):
    download_started = pyqtSignal()
    downloaded_some = pyqtSignal(int)
    downloaded = pyqtSignal(str)
    already_exists = pyqtSignal(str)
    download_done = pyqtSignal(str)
    need_credentials = pyqtSignal()
    error = pyqtSignal(str)
    wrong_credentials = pyqtSignal(str)


class Downloader(QRunnable):
    def __init__(self, url):
        super(Downloader, self).__init__()
        self.signals = DownloaderSigs()
        self.url = url
        self.canceled = False
        self.download_path = get_app_data_folder('downloads')
        self.session = requests
        self.file_size = 0
        self.amount_downloaded = 0

    @pyqtSlot()
    def run(self):
        self.url = self.get_download_path()
        if not self.url:
            return None
        response = self.session.get(self.url, stream=True)
        name = self.check_filename(response)
        if name:
            for root, dirs, files in os.walk(self.download_path):
                if name in files:
                    self.signals.already_exists.emit(os.path.join(root, name))
                else:
                    self.download(name, response)

    def check_filename(self, r):
        try:
            return self.get_filename(r)
        except NotOwnedError as e:
            self.signals.error.emit(str(e))
            self.cancel()
        return None

    def get_file_size(self, headers):
        return headers['Content-length']

    def download(self, name, r):
        file_download_path = f'{self.download_path}\\{name}'
        try:
            self.file_size = self.get_file_size(r.headers)
        except KeyError:
            self.file_size = -1
        amount = 1024 * 1024
        fd = open(file_download_path, 'wb')
        self.signals.download_started.emit()
        for chunk in r.iter_content(amount):
            if self.canceled:
                fd.close()
                self.remove(file_download_path)
                break
            fd.write(chunk)
            self.amount_downloaded += len(chunk)
            self.signals.downloaded_some.emit(self.get_file_progress())
        if not self.canceled:
            fd.close()
            self.signals.download_done.emit(file_download_path)
        else:
            fd.close()
            self.remove(file_download_path)

    def cancel(self):
        self.canceled = True

    def remove(self, file_path):
        try:
            os.remove(file_path)
        except (PermissionError, FileNotFoundError):
            pass

    def get_file_progress(self):
        if not self.file_size == -1:
            return 100*(self.amount_downloaded/int(self.file_size))
        else:
            return -1

    def get_download_path(self):
        return self.url

    def get_filename(self, r):
        return get_title_from_url(self.url)


class PreviewDownloader(Downloader):
    def __init__(self, url, sound_id):
        super(PreviewDownloader, self).__init__(url)
        self.preview_path = get_app_data_folder('Cache')
        self.filename = sound_id

    @pyqtSlot()
    def run(self):
        file_type = self.find_file_type_from_url(self.url)
        name = f'download_{self.filename}.{file_type}'
        for root, dirs, files in os.walk(self.preview_path):
            if name in files:
                self.signals.already_exists.emit(os.path.join(root, name))
            else:
                self.download_preview(self.url, self.filename)

    def find_file_type_from_url(self, url):
        file_type = self.find_file_type_regex(url)
        if file_type == url:
            file_type = url[url.rindex('.')+1:]
        return file_type

    def find_file_type_regex(self, url):
        try:
            file_type = re.search(r'(?<=\.)(.*?\?)', url)
            return self.find_file_type_from_url(file_type.group(0))
        except AttributeError:
            return url.replace('?', '')

    def download_preview(self, url, title):
        file_type = self.find_file_type_from_url(url)
        file_path = f"{self.preview_path}/{title}.{file_type}"
        file_downloader = f"{self.preview_path}/download_{title}.{file_type}"
        amount = 1024*200
        emitted_ready_for_preview = False
        fd = open(file_downloader, 'wb')
        r = requests.get(url, stream=True)
        self.signals.download_started.emit()
        for chunk in r.iter_content(amount):
            if self.canceled:
                fd.close()
                self.remove(file_downloader)
                self.remove(file_path)
                break
            fd.write(chunk)
            if not emitted_ready_for_preview:
                f = open(file_path, 'wb')
                f.write(chunk)
                f.close()
                self.signals.downloaded.emit(file_path)
                emitted_ready_for_preview = True

        if not self.canceled:
            fd.close()
            self.signals.download_done.emit(file_downloader)
        else:
            fd.close()
            self.remove(file_path)


class SoundDogsPreviewDownloader(PreviewDownloader):
    @pyqtSlot()
    def run(self):

        super(SoundDogsPreviewDownloader, self).run()




class AuthDownloader(Downloader):
    def __init__(self, result, credentials):
        super(AuthDownloader, self).__init__('')
        self.result = result
        self.username, self.password = credentials

    @property
    @abstractmethod
    def site_name(self):
        return ''

    def get_download_path(self):
        try:
            return self.session.get_sound_link(self.result)
        except TypeError:
            self.signals.wrong_credentials.emit("Network error! You may want to try different credentials.")


class FreesoundDownloader(AuthDownloader):
    def run(self):
        try:
            self.session = WebsiteAuth.FreeSound(self.username, self.password)
            super(FreesoundDownloader, self).run()
        except WebsiteAuth.LoginError as e:
            self.signals.wrong_credentials.emit(str(e))

    @property
    def site_name(self):
        return 'Freesound'


class ProSoundDownloader(AuthDownloader):
    def run(self):
        try:
            self.session = WebsiteAuth.ProSound(self.username, self.password)
            super(ProSoundDownloader, self).run()
        except WebsiteAuth.LoginError as e:
            self.signals.wrong_credentials.emit(str(e))

    @property
    def site_name(self):
        return 'Pro Sound'

    def get_file_size(self, headers):
        return headers['Content-Length']

    def get_filename(self, r):
        try:
            cd = self.session.get_content_disposition(r)
        except KeyError:
            raise NotOwnedError('You do not own this sound!')
        if not cd:
            return None
        fname = re.findall('filename="(.+)"', cd)
        if len(fname) == 0:
            return None
        return fname[0]


class SoundDogsDownloader(AuthDownloader):
    def run(self):
        try:
            self.session = WebsiteAuth.ProSound(self.username, self.password)
            super(SoundDogsDownloader, self).run()
        except WebsiteAuth.LoginError as e:
            self.signals.wrong_credentials.emit(str(e))

    @property
    def site_name(self):
        return 'Pro Sound'

    def get_file_size(self, headers):
        return headers['Content-Length']

    def get_filename(self, r):
        try:
            cd = self.session.get_content_disposition(r)
        except KeyError:
            raise NotOwnedError('You do not own this sound!')
        if not cd:
            return None
        fname = re.findall('filename="(.+)"', cd)
        if len(fname) == 0:
            return None
        return fname[0]


def get_all_sound_dogs_bought_sound_names(username, password):
    auth_s = WebsiteAuth.SoundDogs(username, password)
    r = auth_s.get("https://www.sounddogs.com/customer/order_history?page=0&orderType=0")
    print(r, r.content)


def get_all_charged_invoices_from_json():
    pass


def freesound_download(threadpool, meta_file, username, password, done_function, progress_function):
    auth_s = WebsiteAuth.FreeSound(username, password)
    downloader = Downloader(auth_s.get_sound_link(meta_file['download link']))
    downloader.session = auth_s
    downloader.signals.downloaded.connect(progress_function)
    downloader.signals.download_done.connect(done_function)
    threadpool.start(downloader)


def get_title_from_url(url):
    return url[url[:-2].rfind('/') + 1:]


def get_sound_dogs_true_duration(track_id):
    r = requests.get(f"https://www.sounddogs.com/mediaPlayer/get_sound_channel_to_by_id/{track_id}")
    return r.json()['sound']['duration']


def pro_sound_get_preview_auth(track_id):
    r = requests.get(f"https://download.prosoundeffects.com/ajax.php?p=download_auth&trackId="
                     f"{track_id}&source=track_list_explorer&type=&embedCode=13")
    return r.json()['content'][0]['params']


get_all_sound_dogs_bought_sound_names('brinkmansound@gmail.com', 'Ferrari578')
