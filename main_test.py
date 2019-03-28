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
#
# sound_file = vlc.MediaPlayer(path_1)
# sound_file.play()

current_time = 0
start = time.time()
while True:
    time.sleep(.01)
    current_time = int((time.time() - start)*1000)
    print(current_time)
    # while sound_file.is_playing():
    #     start = time.time()
    #     time.sleep(7)
    #     print(int((time.time() - start)*1000))
        # sound_time = sound_file.get_time()
        # if sound_time != last_recorded_time:
        #     last_recorded_time = sound_time
        #     last_recorded_time_stamp = time.time()
        #     current_time = sound_time
        #     # print(last_recorded_time_stamp)
        #     # print(current_time, 'New Time Stamp')
        #     # print(sound_file.get_stats(), 'new')
        # else:
        #     # print(last_recorded_time_stamp, time.time())
        #     current_time = int((time.time() - last_recorded_time_stamp)*1000)+last_recorded_time
        #     print(current_time)
        # time.sleep(.01)