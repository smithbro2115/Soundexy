import vlc
import os
import time
import AudioConverter

path_1 = "Z:\\SFX Library\\SoundDogs\\Humvee, Onb,55 MPH,Start Idle Revs,Drive Fast,Uphill Accelerate H,6003_966817.wav"
path_2 = "Z:\\SFX Library\\SoundDogs\\Humvee M998,Pavement,50 MPH,Pass Bys x2 Med Fast,Approach Pothole,5954_966759.wav"
path_3 = "Z:\\SFX Library\\ProSound\\Air Raid Sirens MULTIPLE SIRENS Sound Effect.mp3"
path_4 = "C:\\Users\\Josh\\Desktop\\Audio_Tests\\Airy Static Laser - Copy.Ogg"
path_5 = "C:\\Users\\Josh\\Desktop\\Audio_Tests\\455746__kyles__door-apartment-buzzer-unlock-ext.flac"
path_6 = "https://freesound.org/data/previews/73/73191_806506-lq.mp3"


class VLCPlayer(vlc.MediaPlayer):
    def __init__(self):
        super(VLCPlayer, self).__init__()


print('test')
sound_file = vlc.MediaPlayer(path_1)
sound_file.play()
time.sleep(.5)
print(bool(sound_file.is_playing()))
time.sleep(3)
sound_file.pause()
time.sleep(.5)
print(bool(sound_file.is_playing()))
# length = sound_file.get_length()
# print(sound_file.audio_get_channel())
# sound_file.set_position(.5)

while sound_file.is_playing():
    # print(sound_file.get_time())
    time.sleep(.01)
sound_file.stop()
