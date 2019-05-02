import os
import subprocess
from Soundexy.Functionality.useful_utils import get_app_data_folder


ffmpeg_path = f"{get_app_data_folder('ffmpeg')}/ffmpeg/bin"


def get_pygame_playable_version(sample_rate, channels, path, new_path):
    new = os.path.splitext(new_path)[0] + '.ogg'
    subprocess.call(ffmpeg_path + '/ffmpeg -i "' + path + '" -ac ' + str(channels) + ' -ar ' + str(sample_rate) +
                    ' -y "' + new + '"', stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    return new


def set_channels(channels, path, new_path):
    subprocess.call(ffmpeg_path + '/ffmpeg -i "' + path + '" -ac ' + channels + ' -y "' + new_path + '"',
                    stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    return new_path


def set_sample_rate(sample_rate, path, new_path):
    subprocess.call(ffmpeg_path + '/ffmpeg -i "' + path + '" -ar ' + sample_rate + ' -y "' + new_path + '"',
                    stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    return new_path
