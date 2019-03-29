import vlc
import os
import time
import AudioConverter

path_1 = "C:\\Users\\Josh\\Desktop\\Test Audio Files\\Tree-Fall-Palm-Tree-Heavy-Slow-Cracking-Fall_GEN-HD3.mp3"
path_2 = "Z:\\SFX Library\\SoundDogs\\Humvee M998,Pavement,50 MPH,Pass Bys x2 Med Fast,Approach Pothole,5954_966759.wav"
path_3 = "Z:\\SFX Library\\ProSound\\Air Raid Sirens MULTIPLE SIRENS Sound Effect.mp3"
path_4 = "C:\\Users\\Josh\\Desktop\\Audio_Tests\\Airy Static Laser - Copy.Ogg"
path_5 = "C:\\Users\\Josh\\Desktop\\Audio_Tests\\455746__kyles__door-apartment-buzzer-unlock-ext.flac"
path_6 = "https://freesound.org/data/previews/73/73191_806506-lq.mp3"

# current_time = 0
# last_recorded_time = None
# last_recorded_time_stamp = 0


class Player:
    def __init__(self):
        self.instance = vlc.Instance('--input-repeat=-1', '--fullscreen')
        self.player = self.instance.media_player_new()
        self.start = 0
        self.path = None
        self.current_time = 0

    @property
    def playing(self):
        if self.player.is_playing():
            if self.start == 0:
                self.start = time.time()
            return True
        if not self.start == 0:
            self.current_time = int((time.time() - self.start)*1000)+self.current_time
            self.start = 0
        return False

    def get_time(self):
        if not self.playing:
            return self.current_time
        return int((time.time() - self.start)*1000)+self.current_time

    def load(self, path):
        self.stop()
        self.path = path
        media = self.instance.media_new(path)
        self.player.set_media(media)

    def play(self):
        self.player.play()

    def pause(self):
        self.player.pause()

    def resume(self):
        self.player.pause()

    def stop(self):
        self.start = 0
        self.current_time = 0
        self.player.stop()

    def goto(self, position):
        self.stop()
        self.load(self.path)
        self.play()
        self.player.set_time(round(position))
        self.current_time = position


player = Player()
player.load(path_6)
player.play()
while True:
    while player.playing:
        print(player.get_time())
        current_time = player.get_time()
        if current_time > 4000:
            player.goto(2000)
        time.sleep(.01)
    print(player.get_time())
    time.sleep(.01)
