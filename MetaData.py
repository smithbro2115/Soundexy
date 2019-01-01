import os
from mutagen.id3 import ID3
from mutagen.oggvorbis import OggVorbis


class MetaFile:
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


class OggFile(MetaFile):

    def __init__(self, path):
        self.file = OggVorbis(path)
        super().__init__(path)

    def populate(self):
        super().populate()

    def get_sample_rate(self):
        return self.file.info.sample_rate

    def get_title(self):
        return os.path.basename(self.path)

    def get_description(self):
        return super().description()

    def get_duration(self):
        return super().duration()

    def get_channels(self):
        return super().channels()

    def get_path(self):
        return super().path()

    def get_file_type(self):
        return super().file_type()

    def get_album_image(self):
        return super().album_image()

    def get_bitrate(self):
        return super().bitrate()


test_ogg = OggFile("C:\\Users\\Josh\\Downloads\\133966_2451120-lq.ogg")
print(test_ogg.get_title())
