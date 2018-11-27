import requests
import os
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QRunnable


class DownloaderSigs(QObject):
    download_started = pyqtSignal()
    downloaded = pyqtSignal(str)
    already_exists = pyqtSignal(str)
    download_done = pyqtSignal()


class Downloader(QRunnable):
    def __init__(self, url, title):
        super(Downloader, self).__init__()
        self.signals = DownloaderSigs()
        self.url = url
        self.title = title

    @pyqtSlot()
    def run(self):
        name = self.title + '.mp3'
        path = 'Cache'
        for root, dirs, files in os.walk(path):
            if name in files:
                self.signals.already_exists.emit(os.path.join(root, name))
        self.download_preview(self.url, self.title)

    def download_preview(self, url, title):
        file_path = 'Cache/' + title + '.mp3'
        amount = 1024*200
        emitted_ready_for_preview = False
        fd = open(file_path, 'wb')
        r = requests.get(url, stream=True)
        self.signals.download_started.emit()
        for chunk in r.iter_content(amount):
            fd.write(chunk)
            print('Downloaded some')
            if not emitted_ready_for_preview:
                self.signals.downloaded.emit(file_path)
                emitted_ready_for_preview = True
        fd.close()
        self.signals.download_done.emit()
