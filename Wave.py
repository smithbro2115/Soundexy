import subprocess


def make_waveform(path):
    file_name = 'waveform'

    subprocess.call('ffmpeg -i ' + path + ' -filter_complex "showwavespic=s=1280x240:'
                                          'split_channels=1: colors=#287399" -frames:v 1 -y Waveforms/' + file_name + '.png')
