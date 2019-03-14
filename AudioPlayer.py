import pygame
import MetaData
import os
import time
from random import random
from PyQt5.QtCore import pyqtSignal, QObject, QRunnable, pyqtSlot
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QSlider
from abc import abstractmethod

# TODO Implement selection of a portion
# TODO Allow search results to be dragged on to player
# TODO Allow sound to be dragged into an external program (maybe convert the file if its not a mp3 or wav
# TODO Implement pitching and time shifting


class PlaysoundException(Exception):
    pass


class SoundSigs(QObject):
    time_changed = pyqtSignal()
    set_current_time = pyqtSignal(float)
    reset_cursor = pyqtSignal()
    error = pyqtSignal(str)


class SoundPlayer(QRunnable):
    def __init__(self):
        super(SoundPlayer, self).__init__()
        self.path = ''
        self.waveform = None
        self.label = None
        self.signals = SoundSigs()
        self.wav_list = ['.wav']
        self.pygame_list = ['.flac', '.ogg', '.mp3']
        self.current_result = ''
        self.pixel_time_conversion_rate = 0
        self.audio_player = FullPlayer()
        self.audio_player.signals.error.connect(lambda x: self.signals.error.emit(x))

    def set_waveform(self, waveform):
        self.waveform = waveform

    def set_label(self, label):
        self.label = label

    def handle_download_complete(self, path):
        self.reload(path=path, is_complete=True)

    def space_bar(self):
        if self.audio_player.ended:
            self.audio_player.goto(0)
        elif self.audio_player.playing:
            self.audio_player.pause()
        else:
            self.audio_player.resume()

    @pyqtSlot()
    def run(self):
        while True:
            while self.audio_player.playing and not self.audio_player.ended:
                time.sleep(.003)
                self.signals.time_changed.emit()
            time.sleep(.01)

    def load(self, path, pixel_time_conversion_rate):
        self.pixel_time_conversion_rate = pixel_time_conversion_rate
        file_type = os.path.splitext(path)[1].lower()
        if file_type in self.wav_list:
            self.audio_player = WavPlayer()
        elif file_type in self.pygame_list:
            self.audio_player = PygamePlayer()
        self.audio_player.load(path)

    def load_segment(self, path, true_duration, pixel_time_conversion_rate):
        self.audio_player.stop()
        self.pixel_time_conversion_rate = pixel_time_conversion_rate
        self.audio_player.load_segment(path, true_duration)

    @staticmethod
    def calculate_px_time_conversion_rate(waveform_width, sound_duration):
        return waveform_width/sound_duration

    def goto(self, position):
        self.audio_player.goto(position/self.pixel_time_conversion_rate)
        self.signals.time_changed.emit()


class AudioPlayerSigs(QObject):
    error = pyqtSignal(str)


class AudioPlayer:
    def __init__(self):
        self.signals = AudioPlayerSigs()
        self.loaded = False
        self._playing = False
        self.loop = False
        self.segment = False
        self._path = ''
        self.path = ''
        self._meta_data = None
        self._duration = 0
        self.attempted_current_time = 0
        self.passed_download_head = False
        self._current_time_start = 0
        self.current_time_stop = 0
        self._current_time_stop = 0
        self._current_time = 0
        self.current_time = 0

    @property
    def current_time_stop(self):
        if not self.playing:
            return self._current_time_stop
        return time.time()

    @current_time_stop.setter
    def current_time_stop(self, value):
        self._current_time_stop = value

    @property
    def playing(self):
        return self._playing

    @playing.setter
    def playing(self, value):
        if value:
            self._current_time_start = time.time()
        else:
            self._current_time = self.current_time
            self.current_time_stop = time.time()
            self._current_time_start = time.time()
        self._playing = value

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._path = get_short_path_name(value)

    @property
    def current_time(self) -> int:
        if self.playing:
            return int((self.current_time_stop - self._current_time_start)*1000) + self._current_time
        return self._current_time

    @current_time.setter
    def current_time(self, value):
        self._current_time_start = time.time()
        self._current_time = value

    @property
    def meta_data(self):
        if self.loaded:
            return self._meta_data
        self._meta_data = self.get_meta_file()
        return self._meta_data

    @property
    def true_duration(self):
        return self.meta_data['duration']

    @property
    def duration(self):
        if self.segment:
            return self._duration
        return self.true_duration

    @property
    def ended(self):
        return self.duration <= self.current_time

    def get_meta_file(self):
        return MetaData.get_meta_file(self.path)

    def load(self, path):
        self.path = path
        d = self.duration
        self.loaded = True
        self._load(self.path)

    def _load(self, path):
        pass

    def reload(self, path):
        self.path = path
        self._meta_data = self.get_meta_file()
        self.stop()
        self._reload(path)
        self.loaded = True
        self.play()

    def _reload(self, path):
        pass

    def play(self):
        if not self.playing:
            print(self.playing)
            self.playing = True
            self._play()

    def _play(self):
        pass

    def pause(self):
        if self.playing:
            self.playing = False
            self._pause()

    def _pause(self):
        pass

    def resume(self):
        if not self.playing:
            self.playing = True
            self._resume()

    def _resume(self):
        pass

    def stop(self):
        if self.loaded:
            self._reset()
            self._stop()

    def _stop(self):
        pass

    def goto(self, position):
        self.current_time = position
        if self.segment and position >= self.true_duration:
            self.pause()
            self.attempted_current_time = position
            self.passed_download_head = True
        else:
            self._goto(position)
        if not self.playing:
            self._pause()

    def _goto(self, position):
        pass

    def _reset(self):
        self.loaded = False
        self.playing = False
        self.loop = False
        self.segment = False
        self.passed_download_head = False
        self.current_time = 0

    def end(self):
        if self.loop:
            self.goto(0)
            self.play()

    def swap_file_with_complete_file(self, path):
        if self.passed_download_head:
            current_time = self.attempted_current_time
        else:
            current_time = self.current_time
        self.reload(path)
        self.goto(current_time)

    load_rest_of_segment = swap_file_with_complete_file

    def swap_file_with_incomplete_file(self, path, duration):
        current_time = self.current_time
        self.stop()
        self.load_segment(path, duration)
        self.goto(current_time)
        self.play()

    def load_segment(self, path, duration):
        self.segment = True
        self._duration = duration
        self.load(path)


class WavPlayer(AudioPlayer):
    def __init__(self):
        super(WavPlayer, self).__init__()
        self.alias = ''

    def _load(self, path):
        self.alias = 'playsound_' + str(random())
        self.win_command('open "' + self.path + '" alias', self.alias)
        self.win_command('set', self.alias, 'time format milliseconds')

    def _reload(self, path):
        self._load(path)

    def _play(self):
        self.win_command('play', self.alias, 'from 0 to', str(self.duration))

    def _pause(self):
        self.win_command('pause', self.alias)

    def _resume(self):
        self.win_command('play', self.alias)

    def _stop(self):
        self.win_command('stop', self.alias)

    def _goto(self, position):
        self.win_command('play', self.alias, 'from', str(round(position)), 'to', str(self.duration))

    @staticmethod
    def win_command(*command):
        from ctypes import c_buffer, windll
        from sys import getfilesystemencoding
        buf = c_buffer(255)
        command = ' '.join(command).encode(getfilesystemencoding())
        errorCode = int(windll.winmm.mciSendStringA(command, buf, 254, 0))
        if errorCode:
            errorBuffer = c_buffer(255)
            windll.winmm.mciGetErrorStringA(errorCode, errorBuffer, 254)
            exceptionMessage = ('\n    Error ' + str(errorCode) + ' for command:'
                                                                  '\n        ' + command.decode() +
                                '\n    ' + errorBuffer.value.decode())
            raise PlaysoundException(exceptionMessage)
        return buf.value


class PygamePlayer(AudioPlayer):
    def __init__(self):
        super(PygamePlayer, self).__init__()
        pygame.mixer.init()

    def _load(self, path):
        pygame.mixer.quit()
        frequency = int(self.meta_data['sample rate'])
        channels = int(self.meta_data['channels'])
        pygame.mixer.init(frequency, -16, channels, 512)
        try:
            pygame.mixer.music.load(path)
        except pygame.error:
            self.signals.error.emit("Couldn't play this file!  It may be that it's corrupted.  "
                                    "Try downloading it again.")

    def _reload(self, path):
        try:
            pygame.mixer.music.load(self.path)
        except pygame.error:
            self.signals.error.emit("Couldn't play this file!  It may be that it's corrupted.  "
                                    "Try downloading it again.")

    def _play(self):
        try:
            pygame.mixer.music.play()
        except Exception as e:
            self.signals.error.emit(e)

    def _pause(self):
        pygame.mixer.music.pause()

    def _resume(self):
        pygame.mixer.music.unpause()

    def _stop(self):
        pygame.mixer.music.stop()

    def _goto(self, position):
        pygame.mixer.music.play(start=position/1000)


class WaveformSlider(QSlider):
    def __init__(self, audio_player):
        super(WaveformSlider, self).__init__()
        self.audio_player = audio_player
        self.current_time = 0
        self.previous_time = 0
        self.current_sound_duration = 0
        self.current_result = None
        self.waveform_active = False
        self.background_active = False
        self.is_busy = False
        self.style_sheet_local = ("""
                                     QSlider {background-color: #232629; background-repeat: no-repeat; 
                                     background-position: center;
                                     border: 1px solid #76797c; border-width: 0px;}\n
                                     QSlider::groove:horizontal {height: 400px; margin: 0 0;
                                     background-color: #00ffffff; border: 0px;}\n
                                     QSlider::handle:horizontal {background-color: white;
                                      border: 0px; height: 100px; width: 1px; margin: 0 0;}
                                     """)

        self.busy_indicator = QtGui.QMovie('graphics/busy_indicator.gif')
        self.setStyleSheet(self.style_sheet_local)

    def mousePressEvent(self, event):
        if self.current_result is not None:
            position = QtWidgets.QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), event.x(), self.width())
            self.setValue(position)
            self.audio_player.goto(position)

    def load_result(self, result):
        self.reset_cursor()
        self.current_result = result
        self.current_sound_duration = result.meta_file()['duration']

    def move_to_current_time(self):
        sound_duration = self.current_sound_duration
        current_time = self.audio_player.audio_player.current_time
        # print('main: ' + str(current_time))
        try:
            progress = current_time/sound_duration
        except ZeroDivisionError:
            pass
        else:
            self.setSliderPosition(self.maximum()*progress)

    def reset_cursor(self):
        self.setSliderPosition(0)

    def start_busy_indicator_waveform(self):
        self.is_busy = True
        self.busy_indicator.frameChanged.connect(self.change_frame_busy_indicator_waveform)
        self.busy_indicator.start()

    def change_frame_busy_indicator_waveform(self):
        current_frame = self.busy_indicator.currentPixmap()
        current_frame.save('graphics/current_frame.png', "PNG")
        self.add_file_too_background('graphics/current_frame.png')

    def stop__busy_indicator_waveform(self):
        self.clear_busy_indicator()
        self.busy_indicator.stop()
        self.is_busy = False

    def clear_busy_indicator(self):
        self.style_sheet_local = self.style_sheet_local.replace('graphics/current_frame.png', '')

    def clear_waveform(self):
        self.style_sheet_local = self.style_sheet_local.replace("Waveforms/waveform.png", '')
        self.setStyleSheet(self.style_sheet_local)

    def add_file_too_background(self, file):
        if not self.background_active:
            self.style_sheet_local = self.style_sheet_local + "QSlider {background-image: url(" + file + ");}"
            self.setStyleSheet(self.style_sheet_local)
            self.background_active = True
        else:
            self.style_sheet_local = self.style_sheet_local.replace(
                "QSlider {background-image: url();}",
                "QSlider {background-image: url(" + file + ");}")
            self.setStyleSheet(self.style_sheet_local)

    def add_file_too_border(self, file):
        if not self.waveform_active:
            self.style_sheet_local = self.style_sheet_local + "QSlider {border-image: url(" + file + ");}"
            self.setStyleSheet(self.style_sheet_local)
            self.waveform_active = True
        else:
            self.style_sheet_local = self.style_sheet_local.replace(
                "QSlider {border-image: url();}",
                "QSlider {border-image: url(" + file + ");}")
            self.setStyleSheet(self.style_sheet_local)

    def add_waveform_to_background(self):
        if self.is_busy:
            self.stop__busy_indicator_waveform()
        self.add_file_too_border("Waveforms/waveform.png")


def get_short_path_name(long_name):
    from ctypes import wintypes
    import ctypes
    _GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
    _GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    _GetShortPathNameW.restype = wintypes.DWORD
    """
    Gets the short path name of a given long path.
    http://stackoverflow.com/a/23598461/200291
    """
    output_buf_size = 0
    while True:
        output_buf = ctypes.create_unicode_buffer(output_buf_size)
        needed = _GetShortPathNameW(long_name, output_buf, output_buf_size)
        if output_buf_size >= needed:
            return output_buf.value
        else:
            output_buf_size = needed


def test():
    sound = SoundPlayer()
    sound.load(
        "C:/Users\Josh\Downloads\Humvee,-Onb,55-Mph,Start-Idle-Revs,Drive-Fast,Uphill-Accelerate-H,6003_966817.Wav", 192)
    sound.play()
    time.sleep(5)
    sound.stop()
    sound.load(
        "C:/Users\Josh\Downloads\Humvee-M998,Pavement,50-MPH,Pass-Bys-x2-Med-Fast,Approach-Pothole,5954_966759.wav", 63)
    sound.play()



# test_player = SoundPlayer()
# thread = QThreadPool()
# thread.start(test_player)
# test_player.load('G:\Campground Caper Foley RV\Audio Files\Camper_02.wav', 10000, .011951)
# test_player.play(play_from=2000)
