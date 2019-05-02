from Soundexy.Audio import AudioConverter
import pygame


path = "Z:\\SFX Library\\SoundDogs\\Beirut, Refugee Camp, Med Close Excited Kids, Traffic_1362872.wav"
path_2 = "C:\\Users\\Josh\\Desktop\\Audio_Tests\\Humvee, Onb,55 MPH,Start Idle" \
         " Revs,Drive Fast,Uphill Accelerate H,6003_966817.wav"
path_3 = "C:\\Users\\Josh\\Downloads\\249733__ylearkisto__kotielaimia-pihalla-maalaist" \
         "alo-farmhouse-yard-animals-poultry-a-turkey-sniffing-birds-in-the-bg - Copy.wav"
path_temp = "C:\\Users\\Josh\\Desktop\\Audio_Tests\\temp.wav"
mp3 = "C:\\Users\\Josh\\Desktop\\Test Audio Files\\Tree-Fall-Palm-Tree-Heavy-Slow-Cracking-Fall_GEN-HD3.mp3"

new_path = AudioConverter.get_pygame_playable_version(48000, 2, path, path_temp)
pygame.mixer.pre_init(48000, -16, 2, 1024)
pygame.mixer.init(48000, -16, 2, 1024)
pygame.mixer.music.load(new_path)
pygame.mixer.music.play()
print(pygame.mixer.music.get_volume())
# player = AudioPlayer.PygamePlayer()
# player.load(path)
# player.play()

while True:
    pass
