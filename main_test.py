import AudioConverter
import pygame


path = "C:\\Users\\Josh\\Desktop\\Test Audio Files\\455746__kyles__door-apartment-buzzer-unlock-ext - copy.wav"
path_2 = "C:\\Users\\Josh\\Desktop\\Test Audio Files\\Humvee,-Onb,55-M" \
         "PH,Start-Idle-Revs,Drive-Fast,Uphill-Accelerate-H,6003_966817.wav"
path_3 = "C:\\Users\\Josh\\Downloads\\249733__ylearkisto__kotielaimia-pihalla-maalaist" \
         "alo-farmhouse-yard-animals-poultry-a-turkey-sniffing-birds-in-the-bg - Copy.wav"
path_temp = "C:\\Users\\Josh\\Desktop\\Test Audio Files\\temp.wav"
mp3 = "C:\\Users\\Josh\\Desktop\\Test Audio Files\\Tree-Fall-Palm-Tree-Heavy-Slow-Cracking-Fall_GEN-HD3.mp3"

AudioConverter.get_pygame_playable_version(48000, 2, path_2, path_temp)
pygame.mixer.init()
pygame.mixer.music.load(path_temp)
pygame.mixer.music.play()
print(pygame.mixer.music.get_volume())
# player = AudioPlayer.PygamePlayer()
# player.load(path)
# player.play()

while True:
    pass
