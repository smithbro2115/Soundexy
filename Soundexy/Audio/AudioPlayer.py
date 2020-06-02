from Soundexy.Functionality import useful_utils
import time
from datetime import datetime, timedelta
import traceback
from PyQt5.QtCore import pyqtSignal, QObject, QRunnable, pyqtSlot, QThreadPool
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QSlider
import multi_track_player


# TODO Implement selection of a portion
# TODO Implement pitching and time shifting


class PlaysoundException(Exception):
	pass


class CurrentTime(QRunnable):
	def __init__(self, player):
		super(CurrentTime, self).__init__()
		self.player = player
		self.started_from = timedelta(seconds=0)
		self.current_time = timedelta(seconds=0)
		self.started_playing = datetime.now()
		self._latency = None

	@property
	def latency(self):
		if self._latency:
			return self._latency
		else:
			self._latency = self.player.latency
			return self._latency

	@latency.setter
	def latency(self, value):
		self._latency = value

	@property
	def start_time(self):
		try:
			return self.player.start_time
		except AttributeError:
			return 0

	@pyqtSlot()
	def run(self):
		while True:
			if self.player.state == "playing":
				try:
					self.current_time = timedelta(milliseconds=self.player._player.current_time)
				except (TypeError, AttributeError):
					pass
			time.sleep(.01)

	def paused(self):
		self.current_time = timedelta(milliseconds=self.player._player.current_time)

	def sought(self, value):
		self.current_time = timedelta(milliseconds=value)


class WavPlayer:
	def __init__(self, *args):
		self._player = multi_track_player.PlayerProcess()
		self.thread_pool = QThreadPool()
		self.current_time_tracker = CurrentTime(self)
		self.thread_pool.start(self.current_time_tracker)
		self.pixel_time_conversion_rate = 0
		self.state = "idle"

	def close(self):
		del self._player

	@property
	def current_time(self):
		return self.current_time_tracker.current_time

	@current_time.setter
	def current_time(self, value):
		self.current_time_tracker.sought(value)

	@property
	def playing(self):
		try:
			return self._player.get_playing()
		except AttributeError:
			return False

	@playing.setter
	def playing(self, value):
		pass

	@property
	def start_time(self):
		return self._player.get_start_time()

	@property
	def latency(self):
		return self._player.latency

	def interact(self):
		state = self._player.state
		try:
			if state == "idle":
				self.goto(0)
			elif state == "playing":
				self.pause()
			elif state == "paused":
				self.resume()
		except TypeError:
			traceback.print_exc()

	def play(self):
		self._player.play()
		self.state = "playing"

	def pause(self):
		self._player.pause()
		self.current_time_tracker.paused()
		self.state = "paused"

	def stop(self):
		self.state = "stopping"
		self._player.stop()
		self.current_time = 0
		self.state = "idle"

	def reset(self):
		self.state = "resetting"
		self._player.stop()
		self._player = multi_track_player.PlayerProcess()
		self.current_time = 0
		self.state = "idle"

	def goto(self, position):
		self.state = "seeking"
		goto_time = position / self.pixel_time_conversion_rate
		self._player.goto(goto_time)
		self.current_time = goto_time
		self.state = self._player.state

	def goto_time(self, time_in_milliseconds):
		self._player.goto(time_in_milliseconds)
		self.current_time = time_in_milliseconds

	def load(self, path, pixel_time_conversion_rate, precise_duration=None):
		self.state = "loading"
		self.current_time = 0
		self.pixel_time_conversion_rate = pixel_time_conversion_rate
		self._player.load(path, precise_duration)
		self.state = "idle"

	def reload(self, path, pixel_time_conversion_rate):
		self.stop()
		self.load(path, pixel_time_conversion_rate)

	def resume(self):
		self.play()

	def set_volume(self, value):
		self._player.set_volume(value)

	def set_channels(self, channels):
		self._player.set_channels(channels)


class TimeCheckerSignals(QObject):
	time_changed = pyqtSignal()


class TimeChecker(QRunnable):
	def __init__(self, player):
		super(TimeChecker, self).__init__()
		self.player = player
		self.signals = TimeCheckerSignals()
		self.last_time = None

	@pyqtSlot()
	def run(self):
		while True:
			if self.last_time != self.player.current_time:
				self.last_time = self.player.current_time
				self.signals.time_changed.emit()
			time.sleep(.01)


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
		self.busy_indicator_path = f"{useful_utils.get_app_data_folder('graphics')}/current_frame.png"
		self.style_sheet_local = ("""
		QSlider {background-color: #232629; background-repeat: no-repeat; 
		background-position: center;
		border: 1px solid #76797c; border-width: 0px;}\n
		QSlider::groove:horizontal {height: 400px; margin: 0 0;
		background-color: #00ffffff; border: 0px;}\n
		QSlider::handle:horizontal {background-color: white;
		border: 0px; height: 100px; width: 1px; margin: 0 0;}
		""")
		self.busy_indicator = QtGui.QMovie(f'{useful_utils.get_app_data_folder("graphics")}/busy_indicator.gif')
		self.setStyleSheet(self.style_sheet_local)

	def mousePressEvent(self, event):
		if self.current_result is not None:
			position = QtWidgets.QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), event.x(), self.width())
			previous_time = self.audio_player.current_time
			try:
				self.audio_player.goto(position)
				self.setValue(position)
			except TypeError:
				try:
					self.audio_player.goto(previous_time)
				except TypeError:
					print('Not loaded yet')

	def load_result(self, result):
		self.reset_cursor()
		self.current_result = result
		self.current_sound_duration = result.precise_duration

	def wheelEvent(self, *args, **kwargs):
		pass

	def move_to_current_time(self):
		sound_duration = self.current_sound_duration
		current_time = self.audio_player.current_time.total_seconds()*1000
		try:
			progress = current_time / sound_duration
		except ZeroDivisionError:
			pass
		else:
			self.setSliderPosition(self.maximum() * progress)

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
		current_frame.save(self.busy_indicator_path, "PNG")
		self.add_file_too_background(self.busy_indicator_path)

	def stop__busy_indicator_waveform(self):
		self.clear_busy_indicator()
		self.busy_indicator.stop()
		self.is_busy = False

	def clear_busy_indicator(self):
		self.style_sheet_local = self.style_sheet_local.replace(self.busy_indicator_path, '')

	def clear_waveform(self):
		self.style_sheet_local = self.style_sheet_local.replace(f"{useful_utils.get_app_data_folder('Waveforms')}"
																f"/waveform.png", '')
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
		path = useful_utils.get_app_data_folder('Waveforms')
		self.add_file_too_border(f"{path}/waveform.png")
