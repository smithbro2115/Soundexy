import AudioConverter
import useful_utils
import pygame
import MetaData
import os
import time
import traceback
from random import random
from PyQt5.QtCore import pyqtSignal, QObject, QRunnable, pyqtSlot
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QSlider
import mmap
from ctypes import c_buffer, windll
from sys import getfilesystemencoding

# TODO Implement selection of a portion
# TODO Allow search results to be dragged on to player
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
        self.pygame_list = ['.ogg', '.mp3', '.flac']
        self.current_result = ''
        self.pixel_time_conversion_rate = 0
        self.audio_player = AudioPlayer()
        self.audio_player.signals.error.connect(lambda x: self.signals.error.emit(x))
        self._volume = 85
        self._loop = False

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self.audio_player.set_volume(value)
        self._volume = value

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value):
        self.audio_player.loop = value
        self._loop = value

    def reset(self):
        self.audio_player.stop()
        self.audio_player = AudioPlayerPlaceholder()

    def set_waveform(self, waveform):
        self.waveform = waveform

    def set_label(self, label):
        self.label = label

    def space_bar(self):
        try:
            if self.audio_player.ended:
                self.audio_player.goto(0)
            elif self.audio_player.playing:
                self.audio_player.pause()
            else:
                self.audio_player.resume()
        except TypeError:
            traceback.print_exc()

    @pyqtSlot()
    def run(self):
        while True:
            while self.audio_player.playing and not self.audio_player.ended:
                time.sleep(.003)
                self.signals.time_changed.emit()
            time.sleep(.01)

    def load(self, path, pixel_time_conversion_rate):
        self.pixel_time_conversion_rate = pixel_time_conversion_rate
        self.audio_player = self.get_correct_audio_player(path)
        self.audio_player.load(path)

    def get_correct_audio_player(self, path):
        file_type = os.path.splitext(path)[1].lower()
        # if file_type in self.wav_list:
        #     return WavPlayer(self.volume, self.loop)
        # elif file_type in self.pygame_list:
        return PygamePlayer(self.volume, self.loop)

    def load_segment(self, path, true_duration, pixel_time_conversion_rate):
        current_time = self.audio_player.current_time
        playing = self.audio_player.playing
        self.audio_player.stop()
        self.audio_player = self.get_correct_audio_player(path)
        self.pixel_time_conversion_rate = pixel_time_conversion_rate
        self.audio_player.load_segment(path, true_duration)
        self.audio_player.goto(current_time)
        if playing:
            self.audio_player.play()

    def preload(self, true_duration, pixel_time_conversion_rate):
        self.audio_player.stop()
        self.signals.time_changed.emit()
        self.audio_player = AudioPlayerPlaceholder()
        self.pixel_time_conversion_rate = pixel_time_conversion_rate
        self.audio_player.preload(true_duration)
        self.audio_player.play()

    def reload_sound_from_different_file(self, path):
        current_time = self.audio_player.current_time
        playing = self.audio_player.playing
        self.audio_player.stop()
        self.audio_player = self.get_correct_audio_player(path)
        self.audio_player.load(path)
        if playing:
            self.audio_player.play()
        self.audio_player.goto(current_time)

    @staticmethod
    def calculate_px_time_conversion_rate(waveform_width, sound_duration):
        return waveform_width/sound_duration

    def goto(self, position):
        self.audio_player.goto(position/self.pixel_time_conversion_rate)
        self.signals.time_changed.emit()

    def play(self):
        self.audio_player.play()


class AudioPlayerSigs(QObject):
    error = pyqtSignal(str)


class AudioPlayer:
    def __init__(self, volume=85, loop=False):
        self.signals = AudioPlayerSigs()
        self.loaded = False
        self._playing = False
        self.segment = False
        self._ran_end = False
        self._path = ''
        self.path = ''
        self._original_path = ''
        self._meta_data = None
        self._duration = 0
        self.attempted_current_time = 0
        self.passed_available_time = False
        self.busy = True
        self._current_time_start = 0
        self.current_time_stop = 0
        self._current_time_stop = 0
        self._current_time = 0
        self.current_time = 0
        self._loop = loop
        self._volume = volume

    def __del__(self):
        self._meta_data = None

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value):
        if self.ended and value:
            self.restart()
        self._loop = value

    @property
    def current_time_stop(self):
        if not self.playing or self._ran_end:
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
        self.set_playing(value)

    def set_playing(self, value):
        if value:
            self.set_current_time_start()
        else:
            self._current_time = self.current_time
            self.current_time_stop = time.time()
            self.set_current_time_start()
        self._playing = value

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._original_path = value
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

    def set_current_time_start(self):
        self._current_time_start = time.time()
        return self._current_time_start

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
        if self.duration <= self.current_time:
            if not self._ran_end:
                self.end()
            return True
        else:
            self._ran_end = False
            return False

    def get_meta_file(self):
        return MetaData.get_meta_file(self._original_path)

    def load(self, path):
        self.busy = True
        self.path = self._prepare_file(path)
        self._meta_data = self.get_meta_file()
        self.loaded = True
        self._load(self.path)
        self.busy = False
        self.set_volume(self._volume)

    def _load(self, path):
        pass

    def reload(self, path, playing):
        self.busy = True
        self.path = self._prepare_file(path)
        self._meta_data = self.get_meta_file()
        self.stop()
        self._reload(path)
        self.loaded = True
        self.busy = False
        if playing:
            self.play()
        if self.passed_available_time:
            self.goto(self.attempted_current_time)
            self.passed_available_time = False

    def _reload(self, path):
        pass

    def play(self):
        if not self.playing:
            self.playing = True
            self._play()
            if self.passed_available_time:
                self.goto(self.attempted_current_time)
                self.passed_available_time = False

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

    def set_volume(self, value):
        self._set_volume(value)

    def _set_volume(self, value):
        pass

    def goto(self, position):
        self.current_time = position
        if self.busy and not self.segment:
            self.pause()
            self.attempted_current_time = position
            self.passed_available_time = True
        elif self.segment and position >= self.true_duration:
            self.pause()
            self.attempted_current_time = position
            self.passed_available_time = True
        else:
            if position > self.duration:
                self._goto(self.duration)
            else:
                self._goto(position)

    def _goto(self, position):
        pass

    def _reset(self):
        self.loaded = False
        self.playing = False
        self.loop = False
        self.segment = False
        self.busy = True
        self.passed_available_time = False
        self.current_time = 0

    def end(self):
        if self.loop:
            self.restart()
        self.current_time_stop = time.time()
        self._ran_end = True

    def restart(self):
        self.goto(0)
        self.play()

    def _reload_and_return_previous_time(self, path):
        self.busy = True
        self.path = self._prepare_file(path)
        self._meta_data = self.get_meta_file()
        current_time = self.current_time
        playing = self.playing
        self.stop()
        self._reload(path)
        self.loaded = True
        self.busy = False
        if playing:
            self.play()
        return current_time

    def swap_file_with_complete_file(self, path):
        if self.passed_available_time:
            current_time = self.attempted_current_time
            self.reload(path, self.playing)
        else:
            current_time = self._reload_and_return_previous_time(path)
        self.segment = False
        self.goto(current_time)

    load_rest_of_segment = swap_file_with_complete_file

    def swap_file_with_incomplete_file(self, path, duration):
        pass
        # current_time = self.current_time
        # self.stop()
        # self.current_time = current_time
        # self.load_segment(path, duration)
        # self.goto(current_time)
        # self.play()

    def _prepare_file(self, path):
        return path

    def load_segment(self, path, duration):
        self.segment = True
        self._duration = duration
        self.load(path)


class WavPlayer(AudioPlayer):
    def __init__(self, *args):
        self.alias = ''
        super(WavPlayer, self).__init__(*args)
        self.temp_volume = 0

    def __del__(self):
        self.win_command('close', self.alias)

    def _load(self, path):
        self.alias = 'playsound_' + str(random())
        self.win_command('open "' + self.path + '" alias', self.alias)
        self.win_command('set', self.alias, 'time format milliseconds')

    def _reload(self, path):
        self._load(path)

    def _set_volume(self, value):
        if self.alias != '':
            winmm = windll.LoadLibrary('winmm.dll')
            winmm.waveOutSetVolume(None, value)
            print(value)

    def _play(self):
        self.win_command('play', self.alias, 'from', str(round(self.current_time)), 'to', str(self.duration))

    def _pause(self):
        self.win_command('pause', self.alias)

    def _resume(self):
        self.win_command('play', self.alias)

    def _stop(self):
        self.win_command('stop', self.alias)

    def _goto(self, position):
        self.win_command('play', self.alias, 'from', str(round(position)), 'to', str(self.duration))
        if not self.playing:
            self._pause()

    @staticmethod
    def win_command(*command):
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
    def __init__(self, *args):
        super(PygamePlayer, self).__init__(*args)
        pygame.mixer.pre_init(48000, -16, 2, 1024)
        pygame.mixer.init(48000, -16, 2, 1024)
        self.converted_paths = []
        self.memory_file = None

    def __del__(self):
        self.close_file()
        self.delete_converted_temps()

    def delete_converted_temps(self):
        for _ in range(len(self.converted_paths)):
            path = self.converted_paths.pop()
            useful_utils.try_to_remove_file(path)

    def close_file(self):
        try:
            self.memory_file.close()
        except AttributeError:
            pass

    def set_file(self, path):
        self.close_file()
        with open(path) as f:
            self.memory_file = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

    def set_volume(self, value):
        pygame.mixer.music.set_volume(value/100)

    def _prepare_file(self, path):
        meta = MetaData.get_meta_file(path)
        return self.make_sure_file_is_playable(path, meta)

    def _load(self, path):
        self.set_file(self.path)
        try:
            pygame.mixer.music.load(self.memory_file)
        except pygame.error:
            self.signals.error.emit("Couldn't play this file!  It may be that it's corrupted.  "
                                    "Try downloading it again.")

    def make_sure_file_is_playable(self, path, meta):
        frequency = meta['sample rate']
        channels = meta['channels']
        file_type = meta['file type']
        new_channels = 2 if channels > 2 else channels
        if frequency != 48000 or channels > 2 or file_type not in ('mp3', 'ogg'):
            return self._convert(48000, new_channels, path)
        return path

    def _convert(self, sample_rate, channels, path):
        new_path = 'temp/' + os.path.basename(path)
        new_path = AudioConverter.get_pygame_playable_version(sample_rate, channels, path, new_path)
        self.converted_paths.append(new_path)
        self._meta_data = MetaData.get_meta_file(path)
        return new_path

    def _reload(self, path):
        self.set_file(self.path)
        try:
            pygame.mixer.music.load(self.memory_file)
        except pygame.error:
            self.signals.error.emit("Couldn't play this file!  It may be that it's corrupted.  "
                                    "Try downloading it again.")

    def _play(self):
        try:
            pygame.mixer.music.play()
        except pygame.error as e:
            self.signals.error.emit(e)

    def _pause(self):
        pygame.mixer.music.pause()

    def _resume(self):
        pygame.mixer.music.unpause()

    def _stop(self):
        pygame.mixer.music.stop()
        self.close_file()

    def _goto(self, position):
        try:
            self._reload(self.path)
            pygame.mixer.music.play(start=round(position)/1000)
            if not self.playing:
                self._pause()
        except pygame.error:
            pygame.mixer.music.set_pos(position)


class AudioPlayerPlaceholder(AudioPlayer):
    def __init__(self):
        super(AudioPlayerPlaceholder, self).__init__()
        self.passed_download_head = True

    @property
    def current_time(self):
        return self._current_time

    @current_time.setter
    def current_time(self, value):
        self._current_time = value

    @property
    def ended(self):
        return False

    def goto(self, position):
        self.current_time = position

    def preload(self, duration):
        self._duration = duration
        self.current_time = 0


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
        try:
            progress = current_time/sound_duration
        except ZeroDivisionError:
            pass
        else:
            self.setSliderPosition(self.maximum()*progress)

    def clear_sound(self):
        self.reset_cursor()
        self.current_result = None
        self.clear_waveform()

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
    if not long_name.startswith('http'):
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
    return long_name


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
