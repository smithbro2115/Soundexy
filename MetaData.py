import os
import soundfile as sf
import mutagen.easyid3
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC
from mutagen.mp3 import EasyMP3

# TODO delete result from index when an error is encountered


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
        self._file = None

    @property
    def sample_rate(self):
        return self._file.info.sample_rate

    @property
    def filename(self):
        return os.path.basename(self.path)

    @property
    def title(self):
        return self.get_tag('title')

    @title.setter
    def title(self, title):
        self.set_tag('title', title)

    @property
    def artist(self):
        return self.get_tag('artist')

    @artist.setter
    def artist(self, artist):
        self.set_tag('artist', artist)

    @property
    def url(self):
        return self.get_tag('url')

    @url.setter
    def url(self, url):
        self.set_tag('url', url)

    @property
    def description(self):
        return self.get_tag('description')

    @description.setter
    def description(self, description):
        self.set_tag('description', description)

    @property
    def genre(self):
        return self.get_tag('genre')

    @genre.setter
    def genre(self, genre):
        self.set_tag('genre', genre)

    @property
    def album(self):
        return self.get_tag('album')

    @album.setter
    def album(self, album):
        self.set_tag('album', album)

    @property
    def album_image(self):
        return self.get_tag('cover')

    @property
    def duration(self):
        """In milliseconds"""
        try:
            return round(self._file.info.length * 1000)
        except AttributeError:
            print('Sound has no length')

    @property
    def channels(self):
        return self._file.info.channels

    @property
    def file_type(self):
        return os.path.splitext(self.path)[1]

    @property
    def bitrate(self):
        return self._file.info.bitrate

    def get_tag(self, tag):
        try:
            return self._file[tag][0]
        except (KeyError, TypeError):
            return None

    def set_tag(self, tag, value):
        self._file[tag] = value
        self._file.save()


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
        self.populate()

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
        _file = sf.SoundFile(self.path)
        try:
            self.duration = round((len(_file) / _file.samplerate)*1000)
        except AttributeError:
            print('Sound has no length')
        else:
            self.channels = _file.channels
            self.sample_rate = _file.samplerate

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
    def __init__(self, path):
        super().__init__(path)
        self._file = OggVorbis(path)


class FlacFile(MutagenFile):
    def __init__(self, path):
        super().__init__(path)
        try:
            self._file = FLAC(path)
        except mutagen.flac.FLACNoHeaderError:
            print('File could not be imported')
            raise AttributeError


class Mp3File(MutagenFile):
    def __init__(self, path):
        super().__init__(path)
        try:
            self._file = EasyMP3(path)
        except mutagen.mp3.HeaderNotFoundError:
            print('File Type Not Supported')
            raise AttributeError

    def get_tag(self, tag):
        try:
            return self._file[str(tag)][0]
        except mutagen.easyid3.EasyID3KeyError:
            return None
        except KeyError as e:
            return self.get_tag_second_try(e)

    def get_tag_second_try(self, tag):
        try:
            return self._file[str(tag)][0]
        except KeyError:
            return None


def _test():
    test = Mp3File("C:\\Users\\Josh\\Downloads\\Camping Caper Rough Mix_2.mp3")
    print(test.get_tag('artist'))

