import pygame
import os
import time
from random import random
from PyQt5.QtCore import pyqtSignal, QObject, QRunnable, pyqtSlot, QThreadPool
from PyQt5.QtWidgets import QSlider


class PlaysoundException(Exception):
    pass


class SoundSigs(QObject):
    move_cursor = pyqtSignal(float)
    reset_cursor = pyqtSignal()


class SoundPlayer(QRunnable):
    def __init__(self):
        super(SoundPlayer, self).__init__()
        self.path = ''
        self.is_playing = False
        self.is_paused = False
        self.signals = SoundSigs()
        self.current_result = ''
        self.filetype = ''
        self.alias = ''
        self.windll_list = ['.wav']
        self.pygame_list = ['.flac', '.ogg', '.mp3']
        self.time_started = None
        self.current_time = 0
        self.ended = False
        self.started = False
        self.length = 0
        self.loop = False
        self.pixel_time_conversion_rate = 0

    def handle(self, result, conversion_rate):
        if not self.current_result == result or not self.get_busy():
            self.current_result = result
            self.preload(result, conversion_rate)
        elif self.ended and self.current_result == result:
            self.preload(result, conversion_rate)
        elif self.is_paused:
            self.unpause()
        else:
            self.pause()

    @pyqtSlot()
    def run(self):
        while True:
            while self.is_playing and not self.ended:
                start_time = time.time()
                rate = 1/self.pixel_time_conversion_rate
                sleep_time = rate/1000
                time.sleep(sleep_time)
                stop_time = time.time()
                time_elapsed = (stop_time - start_time)*1000
                self.current_time = self.current_time + time_elapsed
                self.signals.move_cursor.emit(self.current_time)
                if self.current_time >= self.length:
                    self.ended = True

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

    def preload(self, result, conversion_rate):
        busy = self.get_busy()
        if busy:
            self.stop()
        self.load(result.path, result.duration, conversion_rate)
        self.play()

    def load(self, path, length, pixel_time_rate, block=False):
        self.signals.reset_cursor.emit()
        self.path = path
        self.current_time = 0
        self.filetype = os.path.splitext(path)[1].lower()
        self.alias = 'playsound_' + str(random())
        self.length = length
        self.pixel_time_conversion_rate = pixel_time_rate
        if self.filetype in self.windll_list:
            from time import sleep

            print('open "' + self.path + '" alias', self.alias)
            self.win_command('open "' + self.path + '" alias', self.alias)
            self.win_command('set', self.alias, 'time format milliseconds')
            durationInMS = self.win_command('status', self.alias, 'length')

            if block:
                sleep(float(durationInMS) / 1000.0)
        elif self.filetype in self.pygame_list:
            pygame.mixer.init()
            pygame.mixer.music.load(self.path)

    def pause(self):
        if self.filetype in self.windll_list:
            self.win_command('pause', self.alias)
        elif self.filetype in self.pygame_list:
            pygame.mixer.music.pause()
            self.current_time = time.time() - self.time_started + self.current_time
        self.is_playing = False
        self.is_paused = True

    def play(self, play_from=-1):
        self.ended = False
        if self.filetype in self.windll_list:
            if not self.started:
                durationInMS = self.win_command('status', self.alias, 'length')
                self.win_command('play', self.alias, 'from 0 to', durationInMS.decode())
                self.started = True
            if play_from >= 0:
                durationInMS = self.win_command('status', self.alias, 'length')
                self.win_command('play', self.alias, 'from', str(play_from), 'to', durationInMS.decode())
            else:
                self.win_command('play', self.alias)
        elif self.filetype in self.pygame_list:
            if not self.started:
                try:
                    pygame.mixer.music.play()
                except Exception as e:
                    print(e)
                self.started = True
            elif play_from >= 0:
                if self.filetype == '.mp3':
                    pygame.mixer.music.rewind()
                    pygame.mixer.music.set_pos(play_from/1000)
                    pygame.mixer.music.unpause()
                elif self.filetype == '.ogg':
                    pygame.mixer.music.set_pos(play_from / 1000)
                    pygame.mixer.music.unpause()
                elif self.filetype == '.flac':
                    pygame.mixer.music.set_pos(play_from/1000)
                    pygame.mixer.music.unpause()
                self.current_time = play_from/1000
            else:
                pygame.mixer.music.unpause()
        self.time_started = time.time()
        self.is_playing = True
        self.is_paused = False

    unpause = play

    @staticmethod
    def calculate_px_time_conversion_rate(waveform_width, sound_duration):
        return waveform_width/sound_duration

    def get_current_time(self):
        import time
        if self.filetype in self.windll_list:
            self.current_time = float(self.win_command('status', self.alias, 'position'))
            return self.current_time
        elif self.filetype in self.pygame_list:
            if self.is_playing:
                stop_time = time.time()
                self.current_time = self.current_time + stop_time - self.time_started
                return self.current_time
            else:
                return self.current_time * 1000
        if self.current_time >= self.length:
            self.end()

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

    def stop(self):
        if self.filetype in self.windll_list:
            self.win_command('stop', self.alias)
        elif self.filetype in self.pygame_list:
            pygame.mixer.music.stop()
        self.current_time = 0
        self.started = False


class WaveformSlider(QSlider):
    def __init__(self):
        super(WaveformSlider, self).__init__()
        self.current_time = 0
        self.previous_time = 0
        self.current_sound_duration = 0
        self.current_result = None
        self.waveform_active = False
        self.style_sheet_local = ("""
                                     QSlider {background-color: #232629; 
                                     border: 1px solid #76797c; border-width: 0px;}\n
                                     QSlider::groove:horizontal {height: 200px; margin: 0 0;
                                     background-color: #00ffffff; border: 0px;}\n
                                     QSlider::handle:horizontal {background-color: white;
                                      border: 0px; height: 100px; width: 1px; margin: 0 0;}
                                     """)
        self.setStyleSheet(self.style_sheet_local)

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

    def clear_waveform(self):
        self.style_sheet_local = self.style_sheet_local.replace("Waveforms/waveform.png", '')
        self.setStyleSheet(self.style_sheet_local)

    def add_waveform_to_background(self):
        if not self.waveform_active:
            self.style_sheet_local = self.style_sheet_local + "QSlider {border-image: url(Waveforms/waveform.png);}"
            self.setStyleSheet(self.style_sheet_local)
            self.waveform_active = True
        else:
            self.style_sheet_local = self.style_sheet_local.replace(
                "QSlider {border-image: url();}", "QSlider {border-image: url(Waveforms/waveform.png);}")
            self.setStyleSheet(self.style_sheet_local)


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


'''
test_player = SoundPlayer()
thread = QThreadPool()
thread.start(test_player)
test_player.load('C:\\Users\smith\Music\\020 Short Term Missions.mp3', 10000, .011951)
test_player.play()
'''