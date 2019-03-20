from AudioPlayer import SoundPlayer
import time
import os

file_name = "C:\\Users\\Josh\\Desktop\\Audio Tests\\425556__planetronik__rock-808-beat.mp3"
player = SoundPlayer()
player.load(file_name, 1)
player.audio_player.play()
time.sleep(5)
player.audio_player.stop()
player.reset()
os.remove(file_name)
