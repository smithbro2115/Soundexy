from AudioPlayer import SoundPlayer, PygamePlayer
import time
import os
import pygame


file_name = "C:\\Users\\Josh\\Desktop\\Audio Tests\\425556__planetronik__rock-808-beat - Copy.mp3"
file_name_2 = "C:\\Users\\Josh\\Desktop\\Audio Tests\\Cuba, Alley, Roosters Close, Morning, Ext, Multi, Santiago_948398 - Copy.wav"


def test_1():
    player = PygamePlayer()
    player.load(file_name)
    player.play()
    time.sleep(2)
    player.stop()
    player.load(file_name)
    player.play()
    time.sleep(2)
    player.stop()
    os.remove(file_name)


def test_2():
    pygame.mixer.pre_init(frequency=48000)
    pygame.mixer.init()
    pygame.mixer.music.load(file_name)
    pygame.mixer.music.play()
    time.sleep(2)
    pygame.mixer.music.stop()
    pygame.mixer.music.load(file_name)
    pygame.mixer.music.play()
    time.sleep(2)
    pygame.mixer.music.stop()
    pygame.mixer.quit()
    os.remove(file_name)


test_1()
