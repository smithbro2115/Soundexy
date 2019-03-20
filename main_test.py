import pygame
import time
import os
import MetaData

file_name = "C:\\Users\\Josh\\Desktop\\Test Audio Files\\template - Copy.mp3"
meta = MetaData.get_meta_file(file_name)
pygame.mixer.init()
pygame.mixer.music.load(file_name)
pygame.mixer.music.play()
time.sleep(5)
pygame.mixer.music.stop()
pygame.mixer.quit()
os.remove(file_name)
