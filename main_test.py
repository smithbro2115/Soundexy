import pyaudio
import wave
import AudioConverter
import os
import time
from useful_utils import downsample_wav

path_1 = "C:\\Users\\Josh\\Desktop\\Test Audio Files\\Tree-Fall-Palm-Tree-Heavy-Slow-Cracking-Fall_GEN-HD3.mp3"
path_2 = "Z:\\SFX Library\\SoundDogs\\Humvee, Onb,55 MPH,Start Idle Revs,Drive Fast,Uphill Accelerate H,6003_966817.wav"
path_3 = "Z:\\SFX Library\\SoundDogs\\Doors_Vault_Door_38421901.wav"
path_4 = "C:\\Users\\Josh\\Desktop\\Audio_Tests\\Airy Static Laser - Copy.Ogg"
path_5 = "C:\\Users\\Josh\\Desktop\\Audio_Tests\\455746__kyles__door-apartment-buzzer-unlock-ext.flac"
path_6 = "https://freesound.org/data/previews/73/73191_806506-lq.mp3"


class AudioFile:
    chunk = 256

    def __init__(self):
        """ Init audio stream """
        self.wf = None
        self.p = pyaudio.PyAudio()
        self.path = ''
        self.playing = False
        self.converting = False
        self.stream = None

    def load(self, path):
        self.path = path
        file_type = os.path.splitext(self.path)[1]
        if file_type != '.wav':
            self.converting = True
        else:
            self.wf = self.get_wave()
            self.stream = self.p.open(
                format=self.p.get_format_from_width(self.wf.getsampwidth()),
                channels=self.wf.getnchannels(),
                rate=self.wf.getframerate(),
                output=True
            )

    def get_wave(self):
        try:
            return wave.open(self.path, 'rb')
        except wave.Error:
            new_path = self.get_new_path()
            downsample_wav(self.path, new_path, )
            self.path = new_path
            return wave.open(self.path, 'rb')

    def get_new_path(self):
        base_name = os.path.basename(self.path)
        return 'Cache/' + base_name + '.wav'

    def run(self):
        while True:
            while self.playing and not self.converting:
                data = self.wf.readframes(self.chunk)
                while len(data) > 0:
                    print(len(data))
                    self.stream.write(data)
                    data = self.wf.readframes(self.chunk)
            while self.converting:
                new_path = self.get_new_path()
                AudioConverter.convert_to_wav(self.path, new_path)
                self.path = new_path
                self.converting = False
            time.sleep(.01)

    def play(self):
        self.stream.start_stream()
        self.playing = True

    def pause(self):
        self.stream.stop_stream()
        self.playing = False

    def close(self):
        """ Graceful shutdown """
        self.stream.close()
        self.p.terminate()


class AudioFileTest:
    chunk = 256

    def __init__(self, file):
        """ Init audio stream """
        self.wf = wave.open(file, 'rb')
        self.p = pyaudio.PyAudio()
        self.path = file
        self.playing = False
        self.converting = False
        self.ended = False
        self.stream = self.p.open(
            format=self.p.get_format_from_width(self.wf.getsampwidth()),
            channels=self.wf.getnchannels(),
            rate=self.wf.getframerate(),
            output=True
        )

    def run(self):
        while True:
            while self.playing:
                data = self.wf.readframes(self.chunk)
                while len(data) > 0:
                    print(len(data))
                    self.stream.write(data)
                    data = self.wf.readframes(self.chunk)
                print('ended')
                self.ended = True
            while self.converting:
                path, file_type = os.path.splitext(self.path)
                if file_type != '.wav':
                    new_path = path + '.wav'
                    AudioConverter.convert_to_wav(self.path, new_path)
                    self.path = new_path
                self.converting = False
            time.sleep(.01)

    def play(self):
        """ Play entire file """
        self.stream.start_stream()
        self.playing = True

    def pause(self):
        self.stream.stop_stream()
        self.playing = False

    def close(self):
        """ Graceful shutdown """
        self.stream.close()
        self.p.terminate()


# Usage example for pyaudio
a = AudioFile()
a.load(path_3)
a.play()
a.run()
a.close()
