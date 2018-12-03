import GUI
import qdarkstyle
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThreadPool, QRunnable, pyqtSignal, pyqtSlot, QObject
import SearchResults
import re
from AudioPlayer import SoundPlayer, WaveformSlider
import WebScrapers
import LocalFileHandler
import traceback
import Downloader
import os
from Wave import make_waveform
from functools import partial


# TODO make cursor change time on seek
# TODO get website audio to play and generate waveform

class Gui(GUI.Ui_MainWindow):
    def __init__(self):
        self.freesound_thread_pool = QThreadPool()
        self.cursor_pixmap = QtGui.QPixmap('Waveforms/Cursor.png')
        self.cursor_graphic = QtWidgets.QGraphicsPixmapItem()
        self.waveform_thread_pool = QThreadPool()
        self.play_sound_thread_pool = QThreadPool()
        self.local_search_thread_pool = QThreadPool()
        self.local_search_thread_pool.setMaxThreadCount(1)
        self.play_sound_thread_pool.setMaxThreadCount(1)
        self.freesound_thread_pool.setMaxThreadCount(4)
        self.search_state_free = None
        self.search_state_local = None
        self.search_state_paid = None
        self.waveform_active = False
        self.waveform_scene = QtWidgets.QGraphicsScene()
        self.waveform_graphic = None
        self.pixel_time_conversion_rate = 0
        self.previous_time = 0
        self.current_time = 0
        self.search_keywords = ('test', 'test2')
        self.audio_player = SoundPlayer()
        self.current_result = None
        self.running_search = False
        self.running_search_keywords = []
        self.running_search_librarys = {'Free': 0, 'Paid': 0, 'Local': 0}
        self.freesound_amount_of_pages = None
        self.freesound_url = None
        self.row_order = {'Title': 0, 'Description': 1, 'Duration': 2,
                          'Library': 3, 'Author': 4, 'Id': 5}
        self.searchResultsTableModel = QtGui.QStandardItemModel()
        self.cache_thread_pool = QThreadPool()
        self.current_results = {}
        self.waveform = WaveformSlider(self.audio_player)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.waveform.sizePolicy().hasHeightForWidth())
        self.waveform.setSizePolicy(sizePolicy)
        self.waveform.setCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))
        self.waveform.setMaximum(10000)
        self.waveform.setOrientation(QtCore.Qt.Horizontal)
        self.waveform.setObjectName("waveform")
        self.single_clicked_result = None
        self.play_button_graphic = QtGui.QIcon('graphics/play_button_graphic.png')
        self.pause_button_graphic = QtGui.QIcon('graphics/pause_button_graphic.png')

    def setup_ui_additional(self, MainWindow):
        self.search_state_free = self.topbarLibraryFreeCheckbox.checkState()
        self.search_state_local = self.topbarLibraryLocalCheckbox.checkState()
        self.search_state_paid = self.topbarLibraryPaidCheckbox.checkState()
        MainWindow.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.topbarLibraryFreeCheckbox.stateChanged.connect(self.change_free_state)
        self.topbarLibraryLocalCheckbox.stateChanged.connect(self.change_local_state)
        self.topbarLibraryPaidCheckbox.stateChanged.connect(self.change_paid_state)
        # self.topbarLibraryLocalCheckbox.stateChanged.connect(self.search)
        # self.topbarLibraryFreeCheckbox.stateChanged.connect(self.search)
        # self.topbarLibraryPaidCheckbox.stateChanged.connect(self.search)
        self.actionSearch.triggered.connect(self.start_search)
        self.actionPlay.triggered.connect(self.spacebar)
        self.searchResultsTable.setModel(self.searchResultsTableModel)
        headers = sorted(self.row_order, key=self.row_order.get)
        self.searchResultsTableModel.headers = headers
        self.searchResultsTableModel.setHorizontalHeaderLabels(self.searchResultsTableModel.headers)
        self.searchResultsTableModel.setColumnCount(6)
        self.searchResultsTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.searchResultsTable.clicked.connect(self.single_clicked_row)
        self.searchResultsTable.doubleClicked.connect(self.double_clicked_row)
        self.audio_player.signals.move_cursor.connect(self.waveform.move_to_current_time)
        self.audio_player.signals.reset_cursor.connect(self.reset_cursor)
        self.play_sound_thread_pool.start(self.audio_player)
        self.player.layout().addWidget(self.waveform, 0, 1)
        self.playButton.setIcon(self.play_button_graphic)
        self.playButton.setIconSize(QtCore.QSize(24, 24))

    def double_clicked_row(self, signal):
        row_index = signal.row()
        id_column_index = self.row_order['Id']
        sound_id = self.searchResultsTableModel.data(signal.sibling(row_index, id_column_index))
        sound = self.current_results[sound_id]
        if isinstance(sound, SearchResults.Local):
            result = self.current_results[sound_id]
            self.local_sound_init(result)
        elif isinstance(sound, SearchResults.Free or SearchResults.Paid):
            url = self.current_results[sound_id].preview
            downloader = Downloader.Downloader(url, sound_id)
            try:
                downloader.signals.downloaded.connect(self.downloaded_ready_for_preview)
                downloader.signals.already_exists.connect(self.audio_player.handle)
            except Exception as e:
                print(e)
            self.cache_thread_pool.start(downloader)

    def local_sound_init(self, result):
        self.pixel_time_conversion_rate = self.waveform.maximum() / result.duration
        if not self.current_result == result or not self.audio_player.get_busy():
            self.waveform.clear_waveform()
            make_waveform_worker = Worker(make_waveform, result.path)
            make_waveform_worker.signals.finished.connect(self.waveform.add_waveform_to_background)
            self.waveform_thread_pool.start(make_waveform_worker)
            self.waveform.load_result(result)
            self.audio_player.handle(result, self.pixel_time_conversion_rate)
        else:
            self.audio_player.handle(result, self.pixel_time_conversion_rate)
        self.current_result = result


    @staticmethod
    def clear_cache():
        folder = 'Cache'
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)

    def single_clicked_row(self, signal):
        row_index = signal.row()
        id_column_index = self.row_order['Id']
        sound_id = self.searchResultsTableModel.data(signal.sibling(row_index, id_column_index))
        self.single_clicked_result = self.current_results[sound_id]

    def downloaded_ready_for_preview(self, sound_path):
        make_waveform_worker = Worker(make_waveform, sound_path)
        make_waveform_worker.signals.finished.connect(self.waveform.add_waveform_to_background)
        self.waveform_thread_pool.start(make_waveform_worker)
        # self.play_sound(sound_path)

    def spacebar(self):
        if self.current_result is not None:
            if self.current_result != self.single_clicked_result:
                self.local_sound_init(self.single_clicked_result)
            else:
                self.audio_player.handle(self.current_result, conversion_rate=self.pixel_time_conversion_rate)
        elif self.single_clicked_result is not None:
            self.local_sound_init(self.single_clicked_result)

    def reset_cursor(self):
        self.waveform.reset_cursor()

    def freesound_set_url(self, url):
        self.freesound_url = url

    def freesound_set_amount_of_pages(self, amount):
        self.freesound_amount_of_pages = amount

    @staticmethod
    def print_result():
        print('download started')

    def resize_event(self):
        if self.current_result is not None:
            self.pixel_time_conversion_rate = (
                self.audio_player.calculate_px_time_conversion_rate(self.waveform.maximum(),
                                                                    self.current_result.duration))

    def get_waveform_width_minus_margin(self):
        horizontal_margin = self.waveform.contentsMargins().left() + self.waveform.contentsMargins().right()
        return self.waveform.width() - horizontal_margin

    def change_local_state(self):
        self.search_state_local = self.topbarLibraryLocalCheckbox.checkState()

    def change_free_state(self):
        self.search_state_free = self.topbarLibraryFreeCheckbox.checkState()

    def change_paid_state(self):
        self.search_state_paid = self.topbarLibraryPaidCheckbox.checkState()

    def freesound_scrape(self):
        url = self.freesound_url
        amount_of_pages = self.freesound_amount_of_pages
        keywords = self.running_search_keywords
        page_number = 0
        while page_number < amount_of_pages:
            page_number += 1
            freesound_scraper = WebScrapers.FreesoundScraper(keywords, page_number, url)
            freesound_scraper.signals.sig_results.connect(self.add_results_to_search_results_table)
            self.freesound_thread_pool.start(freesound_scraper)

    def add_results_to_search_results_table(self, results):
        for result in results:
            self.current_results[result.id] = result

            title_cell = QtGui.QStandardItem(str(result.title))
            description_cell = QtGui.QStandardItem(str(result.description))
            duration = result.duration/1000
            minutes = duration // 60
            seconds = duration % 60
            duration_cell = QtGui.QStandardItem('%02d:%02d' % (minutes, seconds))
            author_cell = QtGui.QStandardItem(str(result.author))
            library_cell = QtGui.QStandardItem(str(result.library))
            sound_id = QtGui.QStandardItem(str(result.id))
            row = Row(self.row_order, title_cell, author_cell,
                      description_cell, duration_cell, library_cell, sound_id)

            self.searchResultsTableModel.appendRow(row)

    def start_search(self):
        self.search_keywords = self.searchLineEdit
        search_line = self.search_keywords.text()
        current_librarys = {
            'Free': self.search_state_free, 'Paid': self.search_state_paid, 'Local': self.search_state_local
        }

        keywords = re.sub('[^\w-]', ' ', search_line).lower().split()
        excluded_words = []
        for keyword in keywords:
            if keyword.startswith('-'):
                excluded_words.append(keyword[1:])
                keywords.remove(keyword)
            elif '-' in keyword:
                words = re.sub('[^\w]', ' ', keyword).split()
                keywords.remove(keyword)
                for word in words:
                    keywords.append(word)

        if self.running_search_keywords != keywords:
            # if self.running_search:
                # self.freesound_thread_pool.cancel(self.freesound_thread_pool)
            self.run_search(excluded_words)
        elif self.running_search_librarys != current_librarys:
            self.run_search(excluded_words)

    def run_search(self, excluded_words):
        local = self.search_state_local
        free = self.search_state_free
        paid = self.search_state_paid
        search_line = self.search_keywords.text()
        keywords = re.sub('[^\w]', ' ', search_line).lower().split()
        self.search_keywords = keywords
        self.running_search = True
        self.running_search_keywords = keywords
        self.running_search_librarys = {'Free': free, 'Paid': paid, 'Local': local}
        self.searchResultsTableModel.setRowCount(0)
        clear_cache_worker = Worker(self.clear_cache)
        self.cache_thread_pool.start(clear_cache_worker)
        self.current_results = {}
        if local:
            local = LocalFileHandler.LocalSearch(keywords, excluded_words)
            local.signals.batch_found.connect(self.add_results_to_search_results_table)
            self.local_search_thread_pool.start(local)
        if free:
            freesound_site = WebScrapers.Freesound(keywords)
            freesound_site.signals.sig_url.connect(self.freesound_set_url)
            freesound_site.signals.sig_amount_of_pages.connect(self.freesound_set_amount_of_pages)
            freesound_site.signals.sig_finished.connect(self.freesound_scrape)
            self.freesound_thread_pool.start(freesound_site)
        if paid:
            print('test paid ' + str(keywords))


class Window(QtWidgets.QMainWindow):
    resized = QtCore.pyqtSignal()

    def __init__(self, ui, parent=None):
        super(Window, self).__init__(parent=parent)
        self.resized.connect(ui.resize_event)

    def resizeEvent(self, event):
        self.resized.emit()
        return super(Window, self).resizeEvent(event)


class Row(list):
    def __init__(self, order, title, author, description, duration, library, id):
        super().__init__()
        self.title = title
        self.author = author
        self.description = description
        self.duration = duration
        self.library = library
        self.id = id
        for key in order:
            self.append_to_self(key, order[key])

    def append_to_self(self, name, index):
        if name == 'Title':
            self.insert(index, self.title)
        elif name == 'Author':
            self.insert(index, self.author)
        elif name == 'Description':
            self.insert(index, self.description)
        elif name == 'Duration':
            self.insert(index, self.duration)
        elif name == 'Library':
            self.insert(index, self.library)
        elif name == 'Id':
            self.insert(index, self.id)


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker(QRunnable):

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = Gui()
    MainWindow = Window(ui)
    ui.setupUi(MainWindow)
    ui.setup_ui_additional(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
