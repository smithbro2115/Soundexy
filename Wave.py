import subprocess
import os


def make_waveform(path):
    ffmpeg_path = os.path.dirname(os.path.realpath(__file__)) + '/ffmpeg/ffmpeg/bin'
    print(ffmpeg_path)
    file_name = 'waveform'
    subprocess.call(ffmpeg_path + '/ffmpeg -i "' + path + '" -filter_complex "showwavespic=s=1280x240:'
                                                          'split_channels=1: colors=#287399" -frames:v 1 -y Waveforms/'
                    + file_name + '.png')
