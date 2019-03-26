import pydub
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QRunnable
import os


class ConverterSigs(QObject):
    started = pyqtSignal()
    done = pyqtSignal(str)
    error = pyqtSignal(str)


class ConverterRunnable(QRunnable):
    def __init__(self, path):
        super(ConverterRunnable, self).__init__()
        self.signals = ConverterSigs()
        self.path = path

    @pyqtSlot()
    def run(self):
        self.signals.started.emit()
        file_type = os.path.splitext(self.path)[1].lower()
        if file_type == '.flac':
            self.convert_flac_to_wav(self.path)
        elif file_type == '.ogg':
            self.convert_ogg_to_mp3(self.path)
        else:
            self.signals.error.emit('This file type is not supported.')

    def convert_flac_to_wav(self, path):
        sound = pydub.AudioSegment.from_file(path, format='flac')
        new_path = os.path.splitext(path)[0] + '.wav'
        sound.export(new_path, format='wav')
        os.remove(path)
        self.signals.done.emit(new_path)

    def convert_ogg_to_mp3(self, path):
        sound = pydub.AudioSegment.from_file(path, format='ogg')
        new_path = os.path.splitext(path)[0] + '.mp3'
        sound.export(new_path, format='mp3')
        os.remove(path)
        self.signals.done.emit(new_path)


def convert_flac_to_wav(path):
    new_path = os.path.splitext(path)[0] + '.wav'
    get_wav_from_flac(path, new_path)
    os.remove(path)


def convert_ogg_to_mp3(path):
    new_path = os.path.splitext(path)[0] + '.mp3'
    get_mp3_file_from_ogg(path, new_path)
    os.remove(path)


def get_mp3_file_from_ogg(path, new_path):
    print(path, new_path)
    sound = pydub.AudioSegment.from_file(path, format='ogg')
    sound.export(new_path, format='mp3')


def get_wav_from_flac(path, new_path):
    sound = pydub.AudioSegment.from_file(path, format='flac')
    sound.export(new_path, format='wav')


def test_flac():
    file_name = "C:\\Users\\Josh\\Desktop\\Test Audio Files\\455746__kyles__door-apartment-buzzer-unlock-ext - Copy.flac"
    converter = ConverterRunnable()
    converter.convert_flac_to_wav(file_name)


def test_ogg():
    file_name = "C:\\Users\\Josh\\Desktop\\Audio_Tests\\Airy Static Laser - Copy.Ogg"
    converter = ConverterRunnable(file_name)
    converter.convert_ogg_to_mp3(file_name)