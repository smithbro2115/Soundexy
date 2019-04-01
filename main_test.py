import pyaudio
import wave
import AudioConverter
import os
import time

path_1 = "C:\\Users\\Josh\\Desktop\\Test Audio Files\\Tree-Fall-Palm-Tree-Heavy-Slow-Cracking-Fall_GEN-HD3.mp3"
path_2 = "C:\\Users\\Josh\\Desktop\\Test Audio Files\\455746__kyles__door-apartment-buzzer-unlock-ext - copy.wav"
path_3 = "Z:\\SFX Library\\ProSound\\Air Raid Sirens MULTIPLE SIRENS Sound Effect.mp3"
path_4 = "C:\\Users\\Josh\\Desktop\\Audio_Tests\\Airy Static Laser - Copy.Ogg"
path_5 = "C:\\Users\\Josh\\Desktop\\Audio_Tests\\455746__kyles__door-apartment-buzzer-unlock-ext.flac"
path_6 = "https://freesound.org/data/previews/73/73191_806506-lq.mp3"


class AudioFile:
    chunk = 256

    def __init__(self, file):
        """ Init audio stream """
        self.wf = wave.open(file, 'rb')
        self.p = pyaudio.PyAudio()
        self.path = file
        self.playing = False
        self.converting = False
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
                while data != '':
                    self.stream.write(data)
                    data = self.wf.readframes(self.chunk)
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
        data = self.wf.readframes(self.chunk)
        while data != '':
            self.stream.write(data)
            data = self.wf.readframes(self.chunk)

    def close(self):
        """ Graceful shutdown """
        self.stream.close()
        self.p.terminate()


# Usage example for pyaudio
a = AudioFile(path_2)
a.play()
a.close()
