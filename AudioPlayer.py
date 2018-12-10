import pygame
from tinytag import TinyTag
import os
import time
from random import random
from PyQt5.QtCore import pyqtSignal, QObject, QRunnable, pyqtSlot, QThreadPool
from PyQt5 import QtGui, QtWidgets
import SearchResults
from PyQt5.QtWidgets import QSlider


class PlaysoundException(Exception):
    pass


class SoundSigs(QObject):
    time_changed = pyqtSignal(float)
    reset_cursor = pyqtSignal()
    error = pyqtSignal(str)


class SoundPlayer(QRunnable):
    def __init__(self):
        super(SoundPlayer, self).__init__()
        self.path = ''
        self.is_playing = False
        self.is_paused = False
        self.is_segment = False
        self.is_remote = False
        self.time_changed_time_pause = False
        self.reloaded = False
        self.signals = SoundSigs()
        self.current_result = ''
        self.filetype = ''
        self.alias = ''
        self.windll_list = ['.wav']
        self.pygame_list = ['.flac', '.ogg', '.mp3']
        self.time_started = 0
        self.current_time = 0
        self.ended = False
        self.started = False
        self.outside_of_downloaded_range = False
        self.outside_of_downloaded_range_playing = False
        self.length = 0
        self.segment_length = 0
        self.loop = False
        self.pixel_time_conversion_rate = 0
        pygame.mixer.pre_init(48000, -16, 2, 512)

    def remote_sound(self, result, conversion_rate):
        if not self.current_result == result:
            self.current_result = result
            self.pixel_time_conversion_rate = conversion_rate
            self.length = result.duration
            self.is_remote = True
            self.is_segment = True

    def handle_new_sound_local(self):
        self.path = self.current_result.path
        self.preload(self.current_result, self.pixel_time_conversion_rate)
        self.play()

    def handle_new_sound_remote(self, path):
        self.path = path
        self.preload(self.current_result, self.pixel_time_conversion_rate)
        self.play()

    def handle(self, result, conversion_rate, path=None, segment=False):
        if segment:
            self.handle_segment(path, result, conversion_rate)
        elif not self.current_result == result or not self.started:
            self.pixel_time_conversion_rate = conversion_rate
            self.current_result = result
            if isinstance(result, SearchResults.Local):
                self.handle_new_sound_local()
            else:
                self.handle_new_sound_remote(path)
        elif self.ended and self.current_result == result:
            print(self.current_result, result, self.ended)
            self.restart()
        elif self.is_paused:
            self.unpause()
        else:
            self.pause()

    def handle_segment(self, path, result, conversion_rate):
        self.pixel_time_conversion_rate = conversion_rate
        self.current_result = result
        self.path = path
        self.preload(self.current_result, self.pixel_time_conversion_rate, True)
        self.play()

    def handle_download_complete(self, path):
        self.reload(path=path, is_complete=True)

    @pyqtSlot()
    def run(self):
        pass
        while True:
            while self.is_playing and not self.ended:
                start_time = time.time()
                rate = 1/self.pixel_time_conversion_rate
                sleep_time = rate/1000
                time.sleep(sleep_time)
                stop_time = time.time()
                time_elapsed = (stop_time - start_time)*1000
                if self.is_playing:
                    self.set_current_time(self.current_time + time_elapsed)
                if self.current_time >= self.length:
                    self.ended = True
            if not self.is_playing or self.ended:
                time.sleep(.003)

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

    def restart(self):
        print('restart')
        if self.filetype in self.windll_list:
            self.stop()
            self.load_into_windll()
            self.goto(0)
            self.play()
        else:
            self.stop()
            self.reload_into_pygame()
            self.goto(0)
            self.play()

    def preload(self, result, conversion_rate, segment=False):
        busy = self.get_busy()
        if busy:
            self.stop()
        if not self.is_remote:
            self.load(self.path, result.duration, conversion_rate, result.sample_rate)
        else:
            f = TinyTag.get(self.path)
            sample_rate = f.samplerate
            print(sample_rate)
            if segment:
                print('segment 2')
                self.segment_length = f.duration
                self.is_segment = True
                print(self.current_time)
                self.load(self.path, result.duration, conversion_rate, sample_rate, current_time=self.current_time)
            else:
                self.load(self.path, result.duration, conversion_rate, sample_rate)

    def load(self, path, length, pixel_time_rate, sample_rate, block=False, current_time=0):
        self.path = path
        if current_time > 0:
            self.set_current_time(current_time)
        else:
            self.set_current_time(0)
            self.signals.reset_cursor.emit()
        self.filetype = os.path.splitext(path)[1].lower()
        self.length = length
        self.pixel_time_conversion_rate = pixel_time_rate
        if self.filetype in self.windll_list:
            self.load_into_windll(block)
        elif self.filetype in self.pygame_list:
            self.load_into_pygame(sample_rate)

    def load_into_windll(self, block=False):
        from time import sleep

        self.alias = 'playsound_' + str(random())
        print('open "' + self.path + '" alias', self.alias)
        self.win_command('open "' + self.path + '" alias', self.alias)
        self.win_command('set', self.alias, 'time format milliseconds')
        durationInMS = self.win_command('status', self.alias, 'length')

        if block:
            sleep(float(durationInMS) / 1000.0)

    def load_into_pygame(self, sample_rate):
        frequency = int(sample_rate)
        pygame.mixer.quit()
        pygame.mixer.init(frequency, -16, 2, 512)
        try:
            pygame.mixer.music.load(self.path)
        except pygame.error:
            self.signals.error.emit("Couldn't play this file!  It may be that it's corrupted.  "
                                    "Try downloading it again.")

    def reload(self, block=False, path='', is_complete=False):
        print('reloaded')
        self.reloaded = True
        if path != '':
            self.path = path
        if self.filetype in self.windll_list:
            self.reload_into_windll(block)
        elif self.filetype in self.pygame_list:
            self.reload_into_pygame(is_complete)

    def reload_into_windll(self, block=False):
        from time import sleep

        print('open "' + self.path + '" alias', self.alias)
        self.win_command('open "' + self.path + '" alias', self.alias)
        self.win_command('set', self.alias, 'time format milliseconds')
        durationInMS = self.win_command('status', self.alias, 'length')

        if block:
            sleep(float(durationInMS) / 1000.0)

    def reload_into_pygame(self, is_complete=False):
        if is_complete and self.is_segment:
            self.is_segment = False
        was_playing = False
        if self.is_playing:
            self.pause()
            was_playing = True
        pygame.mixer.init()
        try:
            pygame.mixer.music.load(self.path)
        except pygame.error:
            self.signals.error.emit("Couldn't play this file!  It may be that it's corrupted.  "
                                    "Try downloading it again.")
        if was_playing:
            self.outside_of_downloaded_range_playing = False
            self.play()

    def pause(self):
        print('paused')
        if self.filetype in self.windll_list:
            self.win_command('pause', self.alias)
        elif self.filetype in self.pygame_list:
            pygame.mixer.music.pause()
        self.is_playing = False
        self.is_paused = True

    def play_from_pygame(self, play_from):
        if not self.started:
            try:
                pygame.mixer.music.play(start=play_from / 1000)
            except Exception as e:
                print(e)
            self.started = True
        elif play_from > 0:
            try:
                if self.filetype == '.mp3':
                    pygame.mixer.music.rewind()
                pygame.mixer.music.set_pos(play_from / 1000)
                pygame.mixer.music.unpause()
            except pygame.error:
                print('error')
                self.reload()
                pygame.mixer.music.play(start=play_from / 1000)
        else:
            pygame.mixer.music.unpause()

    def play_from_windll(self, play_from):
        if not self.started:
            durationInMS = self.win_command('status', self.alias, 'length')
            self.win_command('play', self.alias, 'from 0 to', durationInMS.decode())
            self.started = True
        if play_from >= 0:
            durationInMS = self.win_command('status', self.alias, 'length')
            self.win_command('play', self.alias, 'from', str(round(play_from)), 'to', durationInMS.decode())
        else:
            self.win_command('play', self.alias)

    def play(self, play_from=-1):
        print('played')
        if play_from > 0:
            self.set_current_time(play_from)
        elif self.time_changed_time_pause or self.reloaded:
            play_from = self.current_time
            self.reloaded = False
        if self.filetype in self.windll_list:
            self.play_from_windll(play_from)
        elif self.filetype in self.pygame_list:
            self.play_from_pygame(play_from)
        self.ended = False
        self.time_started = time.time()
        self.is_playing = True
        self.is_paused = False

    unpause = play

    @staticmethod
    def calculate_px_time_conversion_rate(waveform_width, sound_duration):
        return waveform_width/sound_duration

    def get_current_time(self):
        return self.current_time

    def end(self):
        if self.loop:
            self.play(play_from=0)
        else:
            self.ended = True
            self.is_playing = False

    def get_busy(self):
        if self.started:
            return True
        else:
            return False

    def set_current_time(self, current_time):
        self.signals.time_changed.emit(current_time)
        self.current_time = current_time

    def stop(self):
        if self.filetype in self.windll_list:
            self.win_command('stop', self.alias)
        elif self.filetype in self.pygame_list:
            pygame.mixer.music.stop()
        self.is_playing = False
        self.set_current_time(0)
        self.started = False

    def goto(self, position):
        goto = position/self.pixel_time_conversion_rate
        print(goto)
        if self.is_segment and goto > self.segment_length:
            self.outside_of_downloaded_range = True
            if self.is_playing or not self.started:
                self.outside_of_downloaded_range_playing = True
                self.pause()
        elif self.ended:
            self.play(play_from=goto)
        elif self.is_playing:
            self.pause()
            self.play(play_from=goto)
        elif self.is_paused:
            if not self.outside_of_downloaded_range_playing:
                self.time_changed_time_pause = True
        self.set_current_time(goto)


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
        self.current_sound_duration = result.duration

    def move_to_current_time(self, current_time):
        sound_duration = self.current_sound_duration
        progress = current_time/sound_duration
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
