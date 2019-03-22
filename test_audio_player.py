import AudioPlayer
import unittest
import time


class PygamePlayerTest(unittest.TestCase):
    def setUp(self):
        self.audio_player = AudioPlayer.PygamePlayer()
        self.test_file = "downloads/180389__mrmccormack__limiter-on-hand-crank-music-box-amazing-grace.wav"

    def test_overall(self):
        self.audio_player.load(self.test_file)
        self.audio_player.play()
        while self.audio_player.playing and not self.audio_player.ended:
            print(self.audio_player.current_time)
            time.sleep(.005)


class WavPlayerTest(unittest.TestCase):
    def setUp(self):
        self.audio_player = AudioPlayer.WavPlayer()
        self.test_file = "downloads/180389__mrmccormack__limiter-on-hand-crank-music-box-amazing-grace.wav"

    def test_overall(self):
        self.audio_player.load(self.test_file)
        self.audio_player.play()
        while self.audio_player.playing and not self.audio_player.ended:
            print(self.audio_player.current_time)
            time.sleep(.005)


class FullPlayerTest(unittest.TestCase):
    def setUp(self):
        self.audio_player = AudioPlayer.FullPlayer()
        self.test_file = 'downloads/221869__thatjeffcarter__amazing-grace-beatitudes-chapel.wav'
        self.test_file_2 = \
            "C:\\Users\\Josh\\Downloads\\Tree-Fall-Palm-Tree-Heavy-Slow-Cracking-Fall_GEN-HD3-38085_1398682.mp3"

    def test_overall(self):
        self.audio_player.load(self.test_file)
        self.audio_player.play()
        while self.audio_player.playing and not self.audio_player.ended:
            print(self.audio_player.current_player)
            time.sleep(.005)

    def test_pause(self):
        self.audio_player.load(self.test_file)
        self.audio_player.play()
        print('\nplay')
        time.sleep(6)
        self.audio_player.pause()
        print('pause')
        time.sleep(2)
        self.audio_player.resume()
        print("resume")
        time.sleep(2)
