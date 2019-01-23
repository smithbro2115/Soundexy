import os
import soundfile as sf
import mutagen.easyid3
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC
from mutagen.mp3 import EasyMP3


def get_meta_file(path):
    supported_file_types = {'.mp3': Mp3File, '.wav': WavFile,
                            '.flac': FlacFile, '.ogg': OggFile}
    filetype = os.path.splitext(path)[1].lower()
    try:
        return supported_file_types.get(filetype)(path)
    except KeyError:
        raise AttributeError('File type not supported')


class MutagenFile:
    def __init__(self, path):
        self.path = path
        self.meta = {}
        self.populate()

    def __call__(self, *args, **kwargs):
        return self.meta

    def populate(self):
        file = self.get_file(self.path)
        self.meta['file name'] = self.filename
        self.meta['sample rate'] = self.sample_rate(file)
        self.meta['channels'] = self.channels(file)
        self.meta['duration'] = self.duration(file)
        self.meta['bit rate'] = self.bitrate(file)
        self.meta['file type'] = self.file_type
        self.meta.update(file)

    @staticmethod
    def sample_rate(file):
        return file.info.sample_rate

    @property
    def filename(self):
        return os.path.basename(self.path)

    @staticmethod
    def duration(file):
        """In milliseconds"""
        try:
            return round(file.info.length * 1000)
        except AttributeError:
            print('Sound has no length')

    @staticmethod
    def channels(file):
        return file.info.channels

    @property
    def file_type(self):
        return os.path.splitext(self.path)[1]

    @staticmethod
    def bitrate(file):
        return file.info.bitrate

    def get_tag(self, tag, file):
        try:
            return file[tag][0]
        except (KeyError, TypeError):
            return None

    @staticmethod
    def set_tag(tag, value, file):
        file[tag] = value
        file.save()

    def get_file(self, path):
        pass


class WavFile:
    def __init__(self, path):
        self.path = path
        self.sample_rate = None
        self.duration = None
        self.channels = None
        self.artist = ''
        self.url = ''
        self.genre = ''
        self.album = ''
        self.album_image = None
        self.description = ''
        self.tags = {}
        self.populate()
        self.meta = {}

    def __call__(self, *args, **kwargs):
        return self.meta

    @property
    def title(self):
        return os.path.splitext(self.filename)[0]

    @property
    def filename(self):
        return os.path.basename(self.path)

    @title.setter
    def title(self, title):
        new_dir = os.path.join(os.path.dirname(self.path), title + self.file_type)
        try:
            os.rename(self.path, new_dir)
            self.path = new_dir
        except PermissionError:
            print('Another application is using this file')

    def populate(self):
        self.meta['title'] = self.filename
        self.meta['file name'] = self.filename
        _file = sf.SoundFile(self.path)
        try:
            self.duration = round((len(_file) / _file.samplerate)*1000)
            self.meta['duration'] = self.duration
        except AttributeError:
            print('Sound has no length')
            raise AttributeError
        else:
            self.channels = _file.channels
            self.sample_rate = _file.samplerate
            self.meta['channels'] = self.channels
            self.meta['sample rate'] = self.sample_rate

    @property
    def file_type(self):
        return os.path.splitext(self.path)[1]

    @property
    def bitrate(self):
        return None

    def get_tag(self, tag):
        return ''

    def set_tag(self, tag, value):
        print('wav does not support tags at this point')


class OggFile(MutagenFile):
    def get_file(self, path):
        return OggVorbis(path)


class FlacFile(MutagenFile):
    def get_file(self, path):
        try:
            return FLAC(path)
        except mutagen.flac.FLACNoHeaderError:
            print('File could not be imported')
            raise AttributeError


class Mp3File(MutagenFile):
    def get_file(self, path):
        try:
            return EasyMP3(path)
        except mutagen.mp3.HeaderNotFoundError:
            print('File Type Not Supported')
            raise AttributeError

    def get_tag(self, tag, file):
        try:
            return file[str(tag)][0]
        except mutagen.easyid3.EasyID3KeyError:
            return None
        except KeyError as e:
            return self.get_tag_second_try(e, file)

    @staticmethod
    def get_tag_second_try(tag, file):
        try:
            return file[str(tag)][0]
        except KeyError:
            return None


def _test():
    test = Mp3File("C:\\Users\\Josh\\Downloads\\Camping Caper Rough Mix_2.mp3")
    print(test.get_tag('artist'))

