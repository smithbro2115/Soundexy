import requests
import os
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QRunnable, QThreadPool
import pygame


class DownloaderSigs(QObject):
    download_started = pyqtSignal()
    downloaded = pyqtSignal(str)
    already_exists = pyqtSignal(str)
    download_done = pyqtSignal(str)


class Downloader(QRunnable):
    def __init__(self, url, title):
        super(Downloader, self).__init__()
        self.signals = DownloaderSigs()
        self.url = url
        self.title = title
        self.canceled = False

    @pyqtSlot()
    def run(self):
        name = self.title + '.ogg'
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
                os.remove(file_downloader)
                os.remove(file_path)
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
            self.signals.download_done.emit(file_path)
        elif self.canceled:
            fd.close()
            os.remove(file_path)

    def cancel(self):
        self.canceled = True


def load_pygame(path):
    print('test')
    pygame.mixer.init()
    pygame.mixer.music.load(path)
    play_pygame()


def play_pygame():
    pygame.mixer.music.play()


downloader = Downloader('https://freesound.org/data/previews/77/77727_646701-lq.ogg', 'test')
downloader.signals.downloaded.connect(load_pygame)
thread_pool = QThreadPool()
thread_pool.start(downloader)

while True:
    if input('q'):
        break
