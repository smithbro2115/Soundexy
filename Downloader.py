import requests
import os
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QRunnable
import WebsiteAuth


class DownloaderSigs(QObject):
    download_started = pyqtSignal()
    downloaded = pyqtSignal(str)
    already_exists = pyqtSignal(str)
    download_done = pyqtSignal(str)


class PreviewDownloader(QRunnable):
    def __init__(self, url, title):
        super(PreviewDownloader, self).__init__()
        self.signals = DownloaderSigs()
        self.url = url
        self.title = title
        self.canceled = False

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

    def cancel(self):
        self.canceled = True

    def remove(self, file_path):
        try:
            os.remove(file_path)
        except (PermissionError, FileNotFoundError):
            pass


def freesound_download(threadpool, meta_file, username, password, ):
    auth_s = WebsiteAuth.FreeSound(username, password)
    downloader = PreviewDownloader(auth_s.get_sound_link(meta_file['download link']), meta_file['title'])
    downloader.signals.download_done.connect()
    threadpool.start(downloader)
