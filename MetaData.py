import os
import mutagen.easyid3
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC
from mutagen.mp3 import EasyMP3 as MP3


class MetadataFile:
    def __init__(self, path):
        self.bitrate = 44100
        self.duration = 0
        self.sample_rate = 24
        self.artist = ''
        self.title = ''
        self.description = ''
        self.channels = 0
        self.file_type = ''
        self.path = path
        self.album_image = None

    def populate(self):
        self.file_type = os.path.splitext(self.path)[1]

    def sample_rate(self):
        return self.sample_rate

    def title(self):
        return self.title

    def description(self):
        return self.description

    def duration(self):
        return self.duration

    def channels(self):
        return self.channels

    def path(self):
        return self.path

    def file_type(self):
        return self.file_type

    def album_image(self):
        return self.album_image

    def bitrate(self):
        return self.bitrate


class MutagenFile:
    def __init__(self, path):
        self.path = path
        self.file = None

    def get_sample_rate(self):
        return self.file.info.sample_rate

    def get_title(self):
        return os.path.basename(self.path)

    def get_artist(self):
        self.get_tag('artist')

    def set_artist(self, artist):
        self.set_tag('artist', artist)

    def get_description(self):
        return self.get_tag('description')

    def set_description(self, description):
        self.set_tag('description', description)

    def get_genre(self):
        self.get_tag('genre')

    def set_genre(self, genre):
        self.set_tag('genre', genre)

    def get_duration(self):
        # in milliseconds
        return round(self.file.info.length * 1000)

    def get_channels(self):
        return self.file.info.channels

    def get_path(self):
        return self.path

    def get_file_type(self):
        return os.path.splitext(self.path)[1]

    def get_album_image(self):
        return None

    def get_bitrate(self):
        return self.file.info.bitrate

    def get_tag(self, tag):
        try:
            print('test')
            return self.file[tag]
        except KeyError:
            print('test')
            return None

    def set_tag(self, tag, value):
        self.file[tag] = value
        self.file.save()


class OggFile(MutagenFile):
    def __init__(self, path):
        super().__init__(path)
        self.file = OggVorbis(path)


class FlacFile(MutagenFile):
    def __init__(self, path):
        super().__init__(path)
        self.file = FLAC(path)


class Mp3File(MutagenFile):
    def __init__(self, path):
        super().__init__(path)
        self.file = MP3(path)

    def get_tag(self, tag):
        try:
            print(tag)
            return self.file[tag]
        except mutagen.easyid3.EasyID3KeyError:
            print('error')
            return None


# test_ogg = OggFile("C:\\Users\\Josh\\Downloads\\133966_2451120-lq (1).ogg")
# test_flac = FlacFile("C:\\Users\\Josh\Downloads\\454365__kyles__wind-medium-gusty-cold-winter-wind-swirly-blustery.flac")
test_mp3 = Mp3File("C:\\Users\\Josh\\Downloads\\Sounddogs-Preview-10795957.mp3")
print(test_mp3.get_artist())
