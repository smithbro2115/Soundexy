from wavinfo import WavInfoReader
from tinytag import TinyTag
import soundfile
import chunk

path = "Z:\\SFX Library\\SoundDogs\\Humvee, Onb,55 MPH,Start Idle Revs,Drive Fast,Uphill Accelerate H,6003_966817.wav"
path_2 = "Z:\\SFX Library\\ProSound\\Air_Release_Woosh_PSEF.305.wav"
path_3 = "Z:\\SFX Library\\SoundDogs\\SoldiersMovement 6057_24_286183.wav"
path_4 = "Z:\\SFX Library\\Organized SFX Library\\Human Interaction\\Vine Falling.wav"

print(open(path, 'rb').read(864))
# test_chunk = chunk.Chunk(open(path))
# print(test_chunk)
# wave_obj = WavInfoReader(path_3)
sound_file = soundfile.SoundFile(path)
# sound_file_2 = soundfile.SoundFile(path_4)
# tag = TinyTag.get(path_3)
# print(sound_file.seek(433742787)):
# print(soundfile.read(path, start=soundfile.SEEK_END-834))
print(sound_file.extra_info)
# print(f"\n{sound_file_2.extra_info}")
