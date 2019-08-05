from Soundexy.GUI.API import pyqt_utils
from Soundexy.GUI.DesignerFiles import GUI
import qdarkstyle
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThreadPool, QRunnable, pyqtSignal, pyqtSlot, QObject
import re
from Soundexy.Audio.AudioPlayer import SoundPlayer, WaveformSlider
from Soundexy.Indexing import LocalFileHandler, SearchResults
import traceback
import os
from Soundexy.Imaging.Wave import make_waveform
from Soundexy.GUI.API.CustomPyQtWidgets import SearchResultsTable, DownloadButton, PlaylistTreeWidget, \
    SearchCheckBoxContextMenu, BuyButton
from Soundexy.Indexing.Searches import LocalSearch, FreeSearch, PaidSearch
from Soundexy.Functionality import useful_utils


# TODO Make marking system


class Gui(GUI.Ui_MainWindow):
    def __init__(self):
        self.remote_search_thread_pool = QThreadPool()
        self.waveform_thread_pool = QThreadPool()
        self.play_sound_thread_pool = QThreadPool()
        self.audio_converter_thread_pool = QThreadPool()
        self.local_search_thread_pool = QThreadPool()
        self.local_search_thread_pool.setMaxThreadCount(1)
        self.play_sound_thread_pool.setMaxThreadCount(1)
        self.remote_search_thread_pool.setMaxThreadCount(4)
        self.index_thread_pool = QThreadPool()
        self.index_thread_pool.setMaxThreadCount(1)
        self.current_downloader = None
        self.search_state_free = None
        self.search_state_local = None
        self.search_state_paid = None
        self.waveform_active = False
        self.waveform_scene = QtWidgets.QGraphicsScene()
        self.waveform_graphic = None
        self.index_progress_dialog = None
        self.pixel_time_conversion_rate = 0
        self.previous_time = 0
        self.current_time = 0
        self.search_keywords = ('test', 'test2')
        self.audio_player = SoundPlayer()
        self.current_result = None
        self.running_search = False
        self.running_local_search = False
        self.running_remote_search = False
        self.running_search_keywords = []
        self.running_search_librarys = {'Free': 0, 'Paid': 0, 'Local': 0}
        self.freesound_amount_of_pages = None
        self.freesound_url = None
        self.cache_thread_pool = QThreadPool()
        self.download_pool = QThreadPool()
        self.current_results = {}
        self.playlistTreeWidget = PlaylistTreeWidget()
        self.searchResultsTable = SearchResultsTable()
        self.waveform = WaveformSlider(self.audio_player)
        self.audio_player.set_waveform(self.waveform)
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
        self.busy_indicator_small = QtGui.QMovie(f'{useful_utils.get_app_data_folder("graphics")}/'
                                                 f'busy_indicator_small.gif')
        self.window = None
        self.is_busy_searching = False
        self.background_active_search_indicator = False
        self.waveform_maker = None
        self.local_search = None
        self.remote_searches = []
        self.download_button = DownloadButton()
        self.buyButton = BuyButton()
        self.currently_downloading_results = {}
        self.indexer = LocalFileHandler.Indexer()
        self.converter = None
        self.login = None
        self.freeSearchCheckboxContext = None
        self.paidSearchCheckboxContext = None

    def setup_ui_additional(self, MainWindow):
        self.window = MainWindow
        self.audio_player.set_label(self.currentTimeLabel)
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
        self.actionImport_Directory.triggered.connect(self.open_directory)
        self.actionImport_Audio_File.triggered.connect(self.open_file)
        self.playlistWidgetContainer.addWidget(self.playlistTreeWidget)
        self.playlistAddBtn.clicked.connect(self.playlistTreeWidget.make_playlist)
        self.playlistDeleteBtn.clicked.connect(self.playlistTreeWidget.delete_items)
        self.playlistTreeWidget.double_clicked.connect(lambda x: self.init_sound_by_type(x[0]))
        self.playlistTreeWidget.double_clicked.connect(lambda x: self.single_clicked_playlist_result(x[0]))
        self.playlistTreeWidget.setEditTriggers(QtWidgets.QAbstractItemView.SelectedClicked)
        self.searchResultsTable.clicked.connect(self.single_clicked_row)
        self.searchResultsTable.doubleClicked.connect(self.double_clicked_row)
        self.searchResultsTable.signals.drop_sig.connect(self.open_import_directory)
        self.searchResultsTable.signals.drop_sig.connect(self.open_import_directory)
        self.audio_player.signals.reset_cursor.connect(self.reset_cursor)
        self.audio_player.signals.time_changed.connect(self.set_current_time)
        self.volumeSlider.valueChanged.connect(self.volume_changed)
        self.loopCheckBox.stateChanged.connect(self.loop_changed)
        self.freeSearchCheckboxContext = SearchCheckBoxContextMenu(FreeSearch.__subclasses__(),
                                                                   self.topbarLibraryFreeCheckbox)
        self.paidSearchCheckboxContext = SearchCheckBoxContextMenu(PaidSearch.__subclasses__(),
                                                                   self.topbarLibraryPaidCheckbox)
        self.volumeSlider.setStyleSheet("""QSlider::sub-page:horizontal {
                                        background-color: #287399;
                                        }""")
        self.topbarLibraryFreeCheckbox.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.topbarLibraryFreeCheckbox.customContextMenuRequested.connect(self.free_checkbox_right_clicked)
        self.topbarLibraryPaidCheckbox.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.topbarLibraryPaidCheckbox.customContextMenuRequested.connect(self.paid_search_right_clicked)
        self.audio_player.signals.error.connect(self.show_error)
        self.indexer.signals.started_adding_items.connect(self.open_add_to_index_progress_dialog)
        self.indexer.signals.added_item.connect(self.add_to_index_progress_dialog)
        self.indexer.signals.finished_adding_items.connect(self.close_index_progress_dialog)
        self.play_sound_thread_pool.start(self.audio_player)
        self.player.layout().addWidget(self.waveform, 1, 1)
        self.mainWidget.insertWidget(0, self.searchResultsTable)
        self.searchLineEdit.setStyleSheet("""
                                        QLineEdit{background-repeat: no-repeat; 
                                        background-position: center;}
                                        """)
        self.metaArea.setStyleSheet("""QWidget{background-color: #232629; overflow-y}""")
        self.metaArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.metaTab.layout().insertWidget(1, self.buyButton)
        self.metaTab.layout().insertWidget(2, self.download_button)
        self.buyButton.setHidden(True)
        self.buyButton.button.clicked.connect(lambda: self.buyButton.started())
        self.download_button.setHidden(True)

    def double_clicked_row(self, signal):
        row_index = signal.row()
        id_column_index = self.searchResultsTable.row_order['Id']
        sound_id = self.searchResultsTable.searchResultsTableModel.data(signal.sibling(row_index, id_column_index))
        result = self.searchResultsTable.current_results[sound_id]
        self.init_sound_by_type(result)
        self.single_clicked_result = None

    def init_sound_by_type(self, result):
        if isinstance(result, SearchResults.Local):
            self.local_sound_init(result)
            self.add_album_image_to_player(result.album_image)
        elif isinstance(result, SearchResults.Remote) and not isinstance(result, SearchResults.Paid):
            self.remote_sound_init(result)
        elif isinstance(result, SearchResults.Paid):
            self.paid_sound_init(result)

    def paid_sound_init(self, result: SearchResults.Paid):
        self.add_buy_button(result)
        self.remote_sound_init(result)

    def local_sound_init(self, result):
        self.download_button.setHidden(True)
        self.sound_init(result)

    def remote_sound_init(self, result):
        if result.downloaded and not useful_utils.check_if_file_exists(result.path):
            result.downloaded = False
            result.delete_from_index()
            result.add_to_index()
            self.searchResultsTable.replace_result(result, result)
        self.add_download_button(result)
        if result.downloaded or self.current_result == result:
                self.sound_init(result)
        else:
            self.new_sound_meta(result)
            self.current_result = result
            try:
                self.pixel_time_conversion_rate = self.waveform.maximum() / result.duration
            except ZeroDivisionError:
                self.show_error("This sound can't be played because it has no duration")
            else:
                self.audio_player.preload(result.duration, self.pixel_time_conversion_rate)
                self.new_sound_waveform(result)
                self.current_downloader = self.current_result.download_preview(self.cache_thread_pool,
                                                                               self.current_downloader,
                                                                               self.downloaded_ready_for_preview,
                                                                               self.preview_download_done,
                                                                               self.preview_download_already_exists)

    def sound_init(self, result):
        try:
            self.pixel_time_conversion_rate = self.waveform.maximum() / result.meta_file['duration']
        except ZeroDivisionError:
            self.show_error("This sound can't be played because it has no duration")
        else:
            if not self.current_result == result:
                self.new_sound_meta(result)
                self.make_waveform(result.path)
                self.new_sound_waveform(result)
                self.new_sound_audio_player(result)
            else:
                self.audio_player.space_bar()
        self.current_result = result

    def new_sound_meta(self, result):
        self.clear_meta_tab()
        self.add_metadata_to_meta_tab(result.meta_file)

    def clear_meta_tab(self):
        self.clear_meta_from_meta_tab()
        self.clear_album_image()

    def new_sound_waveform(self, result):
        self.waveform.clear_waveform()
        self.waveform.load_result(result)
        self.waveform.start_busy_indicator_waveform()

    def new_sound_audio_player(self, result):
        self.audio_player.audio_player.stop()
        self.audio_converter_worker(self.audio_player.load, result.path, self.pixel_time_conversion_rate,
                                    finished_f=self.audio_player.play)

    def load_then_play(self, result):
        self.audio_player.load(result.path, self.pixel_time_conversion_rate)
        self.audio_player.play()

    @staticmethod
    def clear_cache():
        folder = useful_utils.get_app_data_folder('Cache')
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)

    def single_clicked_row(self, signal):
        row_index = signal.row()
        id_column_index = self.searchResultsTable.row_order['Id']
        sound_id = self.searchResultsTable.searchResultsTableModel.data(signal.sibling(row_index, id_column_index))
        self.single_clicked_result = self.searchResultsTable.current_results[sound_id]

    def single_clicked_playlist_result(self, result):
        self.single_clicked_result = result

    def add_buy_button(self, result):
        self.buyButton.setHidden(True)
        self.buyButton.reset()
        self.make_buy_button(result)
        self.buyButton.setHidden(False)

    def add_download_button(self, result):
        self.download_button.setHidden(True)
        self.download_button.reset()
        self.make_download_button(result)
        self.download_button.setHidden(False)

    def make_download_button(self, result):
        self.download_button.set_button_function(lambda: result.download(self.download_pool,
                                                                         self.download_started,
                                                                         self.downloaded_some,
                                                                         self.download_done,
                                                                         self.download_button.reset,
                                                                         self.show_error))
        pyqt_utils.disconnect_all_signals(self.download_button.signals.cancel, self.download_button.signals.delete)
        self.download_button.signals.cancel.connect(lambda: result.cancel_download(self.download_button.reset))
        self.download_button.signals.delete.connect(lambda: result.delete_download(self.download_deleted))
        if result.downloaded:
            self.download_button.done()
        if result.downloading:
            self.download_button.set_progress(result.downloader.get_file_progress())
            self.download_button.started()

    def make_buy_button(self, result):
        self.buyButton.set_button_function(lambda: result.buy())
        pyqt_utils.disconnect_all_signals(self.buyButton.signals.cancel)
        self.buyButton.signals.cancel.connect(lambda: result.cancel_buy())
        if result.bought:
            self.buyButton.done()
        if result.buying:
            self.buyButton.started()

    def download_deleted(self):
        self.reset_waveform()
        self.clear_meta_tab()
        self.audio_player.reset()
        self.set_current_time()
        self.download_button.reset()
        self.buyButton.reset()
        self.download_button.setVisible(False)
        self.buyButton.setVisible(False)
        self.searchResultsTable.replace_result(self.current_result, self.current_result)
        self.current_result = None

    def reset_waveform(self):
        self.waveform.clear_sound()

    def downloaded_some(self, progress, result_id):
        if self.current_result.id == result_id:
            self.download_button.set_progress(progress)

    def download_started(self, result_id):
        if self.current_result.id == result_id:
            self.download_button.started()

    def download_done(self, new_result):
        if self.current_result == new_result:
            self.download_button.done()
            self.audio_converter_worker(self.audio_player.audio_player.swap_file_with_complete_file, new_result.path)
        self.searchResultsTable.replace_result(new_result, new_result)

    def converting_audio_done(self, result, new_path):
        result.path = new_path
        result.delete_from_index()
        result.add_to_index()
        self.download_done(result)

    def preview_download_already_exists(self, path):
        self.make_waveform(path)
        self.audio_converter_worker(self.audio_player.load, path, self.pixel_time_conversion_rate,
                                    finished_f=self.audio_player.play)

    def downloaded_ready_for_preview(self, sound_path):
        # self.make_waveform(sound_path)
        self.audio_converter_worker(self.audio_player.load_segment, sound_path,
                                    self.current_result.meta_file['duration'], self.pixel_time_conversion_rate)

    def preview_download_done(self, path):
        self.audio_converter_worker(self.audio_player.audio_player.load_rest_of_segment, path)
        self.make_waveform(path)

    def volume_changed(self):
        self.audio_player.volume = self.volumeSlider.value()

    def loop_changed(self):
        self.audio_player.loop = self.loopCheckBox.checkState()

    def get_indexer(self, paths):
        indexer = LocalFileHandler.Indexer()
        indexer.paths = paths
        indexer.signals.started_adding_items.connect(self.open_add_to_index_progress_dialog)
        indexer.signals.added_item.connect(self.add_to_index_progress_dialog)
        indexer.signals.finished_adding_items.connect(self.close_index_progress_dialog)
        return indexer

    def open_add_to_index_progress_dialog(self):
        self.index_progress_dialog = QtWidgets.QProgressDialog()
        button = QtWidgets.QPushButton()
        button.setStyleSheet('QWidget {background-color: #00ffffff;}')
        button.setDisabled(True)
        self.index_progress_dialog.setWindowTitle('Indexing')
        self.index_progress_dialog.setCancelButton(button)
        self.index_progress_dialog.setStyleSheet("QWidget {background-color: #31363b; color: white;}\n"
                                                 " QProgressBar {background-color: #232629;}")
        self.index_progress_dialog.setAutoClose(True)
        self.index_progress_dialog.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.WindowCloseButtonHint)
        self.index_progress_dialog.setMaximum(0)
        self.index_progress_dialog.setMaximumWidth(500)
        self.index_progress_dialog.setMinimumWidth(499)
        self.index_progress_dialog.setMinimum(0)
        self.index_progress_dialog.setValue(0)
        self.index_progress_dialog.show()

    def add_to_index_progress_dialog(self, title):
        self.index_progress_dialog.setLabelText(title)

    def close_index_progress_dialog(self):
        self.index_progress_dialog.cancel()

    def make_waveform(self, sound_path):
        if self.waveform_thread_pool.activeThreadCount() > 0 and self.waveform_maker is not None:
            self.waveform_maker.interrupt = True
        self.waveform.clear_waveform()
        self.waveform.start_busy_indicator_waveform()
        make_waveform_worker = Worker(make_waveform, sound_path)
        make_waveform_worker.signals.finished.connect(self.waveform.add_waveform_to_background)
        self.waveform_maker = make_waveform_worker
        self.waveform_thread_pool.start(make_waveform_worker)

    def spacebar(self):
        if self.current_result is not None:
            if self.current_result != self.single_clicked_result:
                self.init_sound_by_type(self.single_clicked_result)
            else:
                self.audio_player.space_bar()
        elif self.single_clicked_result is not None:
            self.init_sound_by_type(self.single_clicked_result)

    def reset_cursor(self):
        self.waveform.reset_cursor()

    def audio_converter_worker(self, function, *args, finished_f=None):
        worker = useful_utils.Worker(function, *args)
        if finished_f:
            worker.signals.finished.connect(finished_f)
        self.audio_converter_thread_pool.start(worker)

    @staticmethod
    def get_formatted_time_from_milliseconds(milliseconds):
        minutes = milliseconds // 60000
        seconds = (milliseconds / 1000) % 60
        milliseconds = milliseconds % 1000
        formatted_time = '%02d:%02d:%03d' % (minutes, seconds, milliseconds)
        return formatted_time

    def set_label_text(self, current_time):
        string = 'Current Time: ' + self.get_formatted_time_from_milliseconds(current_time)
        self.currentTimeLabel.setText(string)

    def set_current_time(self):
        current_time = self.audio_player.audio_player.current_time
        self.waveform.move_to_current_time()
        self.set_label_text(current_time)

    def open_directory(self):
        name = QtWidgets.QFileDialog.getExistingDirectory(caption='Open File')
        self.open_import_directory(name)

    def open_file(self):
        name = QtWidgets.QFileDialog.getOpenFileName(caption='Open File')
        self.open_import_audio_file(name)

    def open_import_directory(self, paths):
        try:
            self.indexer.paths = paths
            self.index_thread_pool.start(self.indexer)
        except RuntimeError:
            self.indexer = self.get_indexer(paths)
            self.index_thread_pool.start(self.indexer)
        except TypeError:
            pass

    def open_import_audio_file(self, path):
        try:
            self.indexer.paths = path
            self.index_thread_pool.start(self.indexer)
        except TypeError:
            print('error')
            pass

    def free_checkbox_right_clicked(self, event):
        self.freeSearchCheckboxContext.exec_(self.topbarLibraryFreeCheckbox.mapToGlobal(event))

    def paid_search_right_clicked(self, event):
        self.paidSearchCheckboxContext.exec_(self.topbarLibraryPaidCheckbox.mapToGlobal(event))

    def show_error(self, error):
        msg_box = QtWidgets.QMessageBox()
        msg_box.about(self.window, "ERROR", str(error))

    def clear_album_image(self):
        pixmap = QtGui.QPixmap(1, 0)
        self.playerAlbumImageLbl.setPixmap(pixmap)
        self.metaAlbumImageLbl.setPixmap(pixmap)

    def add_album_image_to_player(self, image):
        if image is not None:
            with open('graphics/temp_album_image.jpg', 'wb') as f:
                f.write(image)
            pixmap = QtGui.QPixmap('graphics\\temp_album_image.jpg')
            pixmap_resized_meta = pixmap.scaled(100, 100, QtCore.Qt.KeepAspectRatio)
            pixmap_resized_player = pixmap.scaled(180, 180, QtCore.Qt.KeepAspectRatio)
            self.metaAlbumImageLbl.setPixmap(pixmap_resized_meta)
            self.playerAlbumImageLbl.setPixmap(pixmap_resized_player)

    def clear_meta_from_meta_tab(self):
        layout = self.metaAreaContents.layout()
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)

    def add_metadata_to_meta_tab(self, result):
        for t, v in result.items():
            if v is not None and v != '':
                tl = QtWidgets.QLabel()
                tl.setText(t.title())
                tl.setStyleSheet("font-weight: bold; font-size: 12px; margin-bottom: 1px;")
                tl.setWordWrap(True)
                tl.setMinimumWidth(self.metaArea.minimumSizeHint().width() + self.metaArea.verticalScrollBar().width())
                self.metaAreaContents.layout().addWidget(tl)
                vl = QtWidgets.QLabel()
                if isinstance(v, list):
                    vl.setText(str(v[0]))
                else:
                    vl.setText(str(v))
                vl.setStyleSheet("margin-bottom: 10px;")
                vl.setMinimumWidth(self.metaArea.minimumSizeHint().width() + self.metaArea.verticalScrollBar().width())
                self.metaAreaContents.layout().addWidget(vl)
                vl.setWordWrap(True)
                tl.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
                tl.setCursor(QtCore.Qt.IBeamCursor)
                vl.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
                vl.setCursor(QtCore.Qt.IBeamCursor)
                tl.show()
                vl.show()

    def resize_event(self):
        if self.current_result is not None:
            self.pixel_time_conversion_rate = (
                self.audio_player.calculate_px_time_conversion_rate(self.waveform.maximum(),
                                                                    self.current_result.meta_file['duration']))

    def get_waveform_width_minus_margin(self):
        horizontal_margin = self.waveform.contentsMargins().left() + self.waveform.contentsMargins().right()
        return self.waveform.width() - horizontal_margin

    def change_local_state(self):
        self.search_state_local = self.topbarLibraryLocalCheckbox.checkState()

    def change_free_state(self):
        self.search_state_free = self.topbarLibraryFreeCheckbox.checkState()

    def change_paid_state(self):
        self.search_state_paid = self.topbarLibraryPaidCheckbox.checkState()

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
        self.start_busy_indicator_search()
        local = self.search_state_local
        free = self.search_state_free
        paid = self.search_state_paid
        search_line = self.search_keywords.text()
        keywords = re.sub('[^\w]', ' ', search_line).lower().split()
        self.search_keywords = keywords
        self.running_search = True
        self.running_search_keywords = keywords
        self.running_search_librarys = {'Free': free, 'Paid': paid, 'Local': local}
        self.searchResultsTable.searchResultsTableModel.setRowCount(0)
        clear_cache_worker = Worker(self.clear_cache)
        self.cache_thread_pool.start(clear_cache_worker)
        self.searchResultsTable.current_results = {}
        if self.running_local_search and self.local_search is not None:
            self.local_search.cancel()
        if local:
            self.running_local_search = True
            self.local_search = LocalFileHandler.IndexSearch(keywords, excluded_words)
            self.local_search.signals.batch_found.connect(self.searchResultsTable.add_results_to_search_results_table)
            self.local_search.signals.finished.connect(lambda: self.finished_search(1))
            self.local_search_thread_pool.start(self.local_search)
        if self.running_remote_search:
            self.cancel_searches(self.remote_searches)
            self.remote_searches = []
        if free:
            for action in self.freeSearchCheckboxContext.actions():
                if action.isChecked():
                    self.running_remote_search = True
                    free_search = action.data()(keywords, excluded_words, self.remote_search_thread_pool)
                    self.remote_searches.append(free_search)
                    free_search.signals.found_batch.connect(self.searchResultsTable.add_results_to_search_results_table)
                    free_search.signals.finished.connect(lambda: self.finished_search(2))
                    free_search.run()
        if paid:
            for action in self.paidSearchCheckboxContext.actions():
                if action.isChecked():
                    self.running_remote_search = True
                    paid_search = action.data()(keywords, excluded_words, self.remote_search_thread_pool)
                    self.remote_searches.append(paid_search)
                    paid_search.signals.found_batch.connect(self.searchResultsTable.add_results_to_search_results_table)
                    paid_search.signals.finished.connect(lambda: self.finished_search(2))
                    paid_search.run()
        if 1 not in (local, free, paid):
            self.finished_search(0)

    def cancel_searches(self, searches):
        for search in searches:
            search.cancel()

    def finished_search(self, search_number):
        if search_number == 1:
            self.running_local_search = False
        elif search_number == 2:
            if self.remote_search_thread_pool.activeThreadCount() == 0:
                self.running_remote_search = False
                self.remote_searches = []
        if 1 not in (self.running_remote_search, self.running_local_search):
            self.stop__busy_indicator_search()

    def start_busy_indicator_search(self):
        self.is_busy_searching = True
        self.busy_indicator_small.frameChanged.connect(self.change_frame_busy_indicator_search)
        self.busy_indicator_small.start()

    def change_frame_busy_indicator_search(self):
        current_frame = self.busy_indicator_small.currentPixmap()
        path = f'{useful_utils.get_app_data_folder("graphics")}/current_frame_small.png'
        current_frame.save(path, "PNG")
        self.add_file_too_background(path)

    def stop__busy_indicator_search(self):
        self.clear_busy_indicator()
        self.busy_indicator_small.stop()
        self.is_busy_searching = False

    def clear_busy_indicator(self):
        self.searchLineEdit.setStyleSheet(self.searchLineEdit.styleSheet().replace(
            f'{useful_utils.get_app_data_folder("graphics")}/current_frame_small.png', ''))

    def add_file_too_background(self, file):
        if not self.background_active_search_indicator:
            style_sheet_local = self.searchLineEdit.styleSheet() + "QLineEdit {background-image: url(" + file + ");}"
            self.searchLineEdit.setStyleSheet(style_sheet_local)
            self.background_active_search_indicator = True
        else:
            style_sheet_local = self.searchLineEdit.styleSheet().replace(
                "QLineEdit {background-image: url();}",
                "QLineEdit {background-image: url(" + file + ");}")
            self.searchLineEdit.setStyleSheet(style_sheet_local)


class Window(QtWidgets.QMainWindow):
    resized = QtCore.pyqtSignal()

    def __init__(self, ui, parent=None):
        super(Window, self).__init__(parent=parent)
        self.resized.connect(ui.resize_event)
        self.settings = QtCore.QSettings('smithbro', 'App')
        try:
            self.restoreGeometry(self.settings.value('geometry'))
            self.restoreState(self.settings.value('windowState', ''))
        except TypeError:
            pass

    def resizeEvent(self, event):
        self.resized.emit()
        return super(Window, self).resizeEvent(event)

    def closeEvent(self, event):
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())
        QtWidgets.QMainWindow.closeEvent(self, event)
        useful_utils.clear_folder(useful_utils.get_app_data_folder('temp'))
        useful_utils.clear_folder(useful_utils.get_app_data_folder('Cache'))


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

        self.interrupt = False

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
            if not self.interrupt:
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
