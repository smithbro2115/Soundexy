import subprocess
from Soundexy.Functionality.useful_utils import get_app_data_folder


def make_waveform(path):
    ffmpeg_path = f"{get_app_data_folder('ffmpeg')}/ffmpeg/bin"
    file_name = f'{get_app_data_folder("Waveforms")}/waveform.png'
    subprocess.call(ffmpeg_path + '/ffmpeg -i "' + path + '" -filter_complex "showwavespic=s=1280x240:'
                                                          'split_channels=1: colors=#287399" -frames:v 1 -y '
                    + file_name, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
