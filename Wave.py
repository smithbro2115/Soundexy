import subprocess
import os


def make_waveform(path):
    ffmpeg_path = os.path.dirname(os.path.realpath(__file__)) + '/ffmpeg/ffmpeg/bin'
    print(path)
    file_name = 'waveform'
    subprocess.Popen('ipconfig', cwd=ffmpeg_path)
