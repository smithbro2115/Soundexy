from AudioPlayer import SoundPlayer, PygamePlayer
import time
import os
import pygame


file_name = "C:\\Users\\Josh\\Desktop\\Test Audio Files\\Tree-Fall-Palm-Tree-Heavy-Slow-Cracking-Fall_GEN-HD3 - Copy.mp3"
file_name_2 = "C:\\Users\\Josh\\Desktop\\Audio Tests\\Cuba, Alley, Roosters Close, Morning, Ext, Multi, Santiago_948398 - Copy.wav"


def test_1():
    player = PygamePlayer()
    player.load(file_name)
    player.play()
    time.sleep(2)
    player.stop()
    player = PygamePlayer()
    player.load(file_name)
    player.play()
    time.sleep(2)
    player.stop()
    player = None
    # pygame.mixer.quit()
    time.sleep(1)
    os.remove(file_name)


def test_2():
    player = PygamePlayer()
    player.load(file_name)
    player.play()
    time.sleep(2)
    player.stop()
    player.load(file_name)
    player.play()
    time.sleep(2)
    player = None
    os.remove(file_name)


def test_3():
    player = SoundPlayer()
    player.load(file_name, 1)
    player.audio_player.play()
    time.sleep(2)
    player.audio_player.stop()
    player.load(file_name, 1)
    player.audio_player.play()
    time.sleep(2)
    player.reset()
    os.remove(file_name)


test_3()
