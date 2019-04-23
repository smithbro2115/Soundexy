import AudioPlayer
import useful_utils
from PyQt5.QtCore import QThreadPool
import time


def test_f(path):
    return useful_utils.get_file_type_from_path(path)


path = "C:\\Users\\Josh\\Desktop\\Test Audio Files\\455746__kyles__door-apartment-buzzer-unlock-ext - copy.wav"


print(test_f(path))