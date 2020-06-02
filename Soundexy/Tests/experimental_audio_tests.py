import pydub
import miniaudio
import numpy as np
from time import sleep
import sounddevice as sd
import math
import requests
from matplotlib import pyplot

PATH = "C:\\Users\\smith\\Desktop\\Air Raid Sirens MULTIPLE SIRENS Sound Effect.mp3"
URL = "https://freesound.org/data/previews/328/328165_5121236-lq.mp3"
BUFFER = None
HEADER = ""
SAMPLE_RATE = 24000
CHANNELS = 2
headers = {"range": f"bytes=176140-"}
r = requests.get(URL, headers=headers, stream=True,)
print(r.headers)

i = 0
# print("started")
# stream = miniaudio.decode_file(PATH)
# print(stream.samples)
# with miniaudio.PlaybackDevice() as device:
# 	device.start(stream)
# 	input("Audio file playing in the background. Enter to stop playback: ")
# for chunk in r.iter_content(1024 * 1024):
# 	# if i == 0:
# 	# 	info = miniaudio.mp3_get_info(chunk)
# 	# 	SAMPLE_RATE = info.sample_rate
# 	# 	CHANNELS = info.nchannels
# 	# 	print(SAMPLE_RATE, CHANNELS)
# 	decoder = miniaudio.decode(chunk, sample_rate=SAMPLE_RATE, nchannels=CHANNELS)
# 	audio_array = np.array(decoder.samples)
# 	new_array = audio_array.reshape((math.ceil(len(audio_array)/decoder.nchannels), decoder.nchannels))
# 	try:
# 		BUFFER = np.concatenate((BUFFER, new_array))
# 	except ValueError:
# 		BUFFER = new_array
# 	i += 1
#
# # audio_segment = pydub.AudioSegment.from_file(
# # 	"Z:/SFX Library/Digital Juice/Digital Juice Files/SFX_V03D02D\\General\\"
# # 	"Animals\\Animals Horse Gallop Left To Right Hard Surface.Wav")
# # audio_segment = pydub.AudioSegment.from_file(BytesIO(BUFFER))
# # print(BUFFER)
# # audio_array = np.array(stream.samples)
# # new_array = audio_array.reshape((math.ceil(len(audio_array)/stream.nchannels), stream.nchannels))
# # print(new_array)
#
#

stream = miniaudio.mp3_stream_file(PATH)
info = miniaudio.mp3_get_file_info(PATH)
for chunk in stream:
	audio_array = np.array(chunk)
	new_array = audio_array.reshape((math.ceil(len(audio_array)/info.nchannels), info.nchannels))
	plot = pyplot.plot(audio_array)
	try:
		BUFFER = np.concatenate((BUFFER, new_array))
	except ValueError:
		BUFFER = new_array



sd.play(BUFFER, samplerate=SAMPLE_RATE)
pyplot.figure(1)
pyplot.title("Signal Wave...")
pyplot.plot(BUFFER)
pyplot.show()
# print(sd.get_stream().dtype)
#
# print(sd.query_devices())
while True:
	sleep(2)
