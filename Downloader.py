import requests
import os
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QRunnable
import WebsiteAuth
import time


class DownloaderSigs(QObject):
    download_started = pyqtSignal()
    downloaded_some = pyqtSignal(int)
    downloaded = pyqtSignal(str)
    already_exists = pyqtSignal(str)
    download_done = pyqtSignal(str)


class Downloader(QRunnable):
    def __init__(self, url):
        super(Downloader, self).__init__()
        self.signals = DownloaderSigs()
        self.url = url
        self.canceled = False
        self.download_path = None
        self.session = requests
        self.file_size = 0
        self.amount_downloaded = 0

    @pyqtSlot()
    def run(self):
        name = get_title_from_url(self.get_download_path())
        print(self.get_download_path())
        for root, dirs, files in os.walk(self.download_path):
            if name in files:
                self.signals.already_exists.emit(os.path.join(root, name))
            else:
                self.download(name)

    def download(self, name):
        file_download_path = f'{self.download_path}\\{name}'
        try:
            self.file_size = self.session.get(self.get_download_path(), stream=True).headers['Content-length']
        except KeyError:
            self.file_size = -1
        amount = 1024 * 200
        fd = open(file_download_path, 'wb')
        r = self.session.get(self.get_download_path(), stream=True)
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
            print(self.amount_downloaded, time.time())
            return 100*(self.amount_downloaded/int(self.file_size))
        else:
            return -1

    def get_download_path(self):
        return self.url


class PreviewDownloader(Downloader):
    def __init__(self, url, title):
        super(PreviewDownloader, self).__init__(url)
        self.title = title

    @pyqtSlot()
    def run(self):
        name = 'download_' + self.title + '.ogg'
        path = 'Cache'
        for root, dirs, files in os.walk(path):
            if name in files:
                self.signals.already_exists.emit(os.path.join(root, name))
            else:
                self.download_preview(self.url, self.title)

    def download_preview(self, url, title):
        file_path = 'Cache/' + title + '.ogg'
        file_downloader = 'Cache/download_' + title + '.ogg'
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
                print('downloaded some')
                self.signals.downloaded.emit(file_path)
                emitted_ready_for_preview = True

        if not self.canceled:
            fd.close()
            print('download done')
            self.signals.download_done.emit(file_downloader)
        else:
            fd.close()
            self.remove(file_path)


class AuthDownloader(Downloader):
    def __init__(self, url, username, password):
        super(AuthDownloader, self).__init__(url)
        self.session = WebsiteAuth.FreeSound(username, password)

    def get_download_path(self):
        return self.session.get_sound_link(self.url)


def freesound_download(threadpool, meta_file, username, password, done_function, progress_function):
    auth_s = WebsiteAuth.FreeSound(username, password)
    downloader = Downloader(auth_s.get_sound_link(meta_file['download link']))
    downloader.session = auth_s
    downloader.signals.downloaded.connect(progress_function)
    downloader.signals.download_done.connect(done_function)
    threadpool.start(downloader)


def get_title_from_url(url):
    return url[url[:-2].rfind('/') + 1:]
