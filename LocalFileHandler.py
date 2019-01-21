import os
import pickle
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QRunnable, QThreadPool
from SearchResults import Local


class IndexerSigs(QObject):
    started_adding_items = pyqtSignal()
    added_item = pyqtSignal(str)
    finished_adding_items = pyqtSignal()
    deleted_item = pyqtSignal(str)
    error = pyqtSignal(str)


class Indexer(QRunnable):
    def __init__(self, paths):
        super(Indexer, self).__init__()
        self.excepted_file_types = ['.mp3', '.wav', '.flac', '.ogg']
        self.index_file_name = 'local_index'
        self.signals = IndexerSigs()
        self.paths = paths
        self.index_paths = []
        self.index = []
        self.emitted_start_adding_items = False

    @staticmethod
    def load_obj(name):
        try:
            with open('obj/' + name + '.pkl', 'rb') as f:
                return pickle.load(f)
        except EOFError:
            return []

    @staticmethod
    def save_obj(obj, name):
        with open('obj/' + name + '.pkl', 'wb') as f:
            try:
                pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
            except TypeError:
                raise AttributeError

    @staticmethod
    def emit_signal_if_condition_false(signal: pyqtSignal, condition: bool):
        if not condition:
            signal.emit()
            return True
        else:
            return False

    def emit_started_adding_items(self):
        if self.emit_signal_if_condition_false(self.signals.started_adding_items, self.emitted_start_adding_items):
            print('test')
            self.emitted_start_adding_items = True

    def run(self):
        try:
            self.index = self.load_obj(self.index_file_name)
        except FileNotFoundError:
            self.save_obj(self.index, self.index_file_name)
            print('Made New Index File')
        finally:
            self.index_paths = []
            for i in self.index:
                self.index_paths.append(i.path)
            if len(self.paths) > 1:
                self.add_multiple_paths_to_index(self.paths)
            else:
                print('test')
                self.add_path_to_index(self.paths[0])

    def add_multiple_paths_to_index(self, paths):
        self.emit_started_adding_items()
        for path in paths:
            self.add_path_to_index(path, emit_when_added=True)
        self.signals.finished_adding_items.emit()

    def add_path_to_index(self, path, emit_when_added=False):
        if os.path.isdir(path):
            self.emit_started_adding_items()
            self.add_dir_to_index(path, emit_when_added=True)
        else:
            self.add_single_to_index(path, emit_when_added=emit_when_added)

    def add_dir_to_index(self, path, emit_when_added=False):
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file.title())
                self.add_single_to_index(file_path, emit_when_added=emit_when_added)
            if len(self.paths) > 1:
                self.signals.finished_adding_items.emit()

    def add_single_to_index(self, path, emit_when_added=False):
        if self.determine_if_file_should_be_added_to_index(path, self.index_paths):
            self.append_to_index(self.index, path)
            self.save_obj(self.index, self.index_file_name)
            if emit_when_added:
                self.signals.added_item.emit(path)

    @staticmethod
    def append_to_index(index, file_path):
        i = 'L%08d' % len(index)
        local_result = Local()
        if local_result.populate(file_path, i):
            print('passed')
            index.append(local_result)

    def determine_if_file_should_be_added_to_index(self, file_path, index_paths):
        extension = os.path.splitext(file_path)[1]
        if extension.lower() in self.excepted_file_types:
            if file_path not in index_paths:
                return True
            else:
                return False

    def delete_from_index(self, result):
        try:
            index = self.load_obj(self.index_file_name)
        except FileNotFoundError as e:
            self.signals.error.emit(e)
        else:
            try:
                index.pop(result)
                self.save_obj(index, self.index_file_name)
                self.signals.deleted_item(result)
            except KeyError as e:
                self.signals.error.emit(e)


class LocalSearchSigs(QObject):
    started = pyqtSignal()
    batch_found = pyqtSignal(list)
    finished = pyqtSignal()


class LocalSearch(QRunnable):
    def __init__(self, keywords, excluded_words, index_path='local_index', batch_amount=15):
        super(LocalSearch, self).__init__()
        self.keywords = keywords
        self.signals = LocalSearchSigs()
        self.index_path = index_path
        self.batch_amount = batch_amount
        self.excluded_words = excluded_words
        self.canceled = False

    @staticmethod
    def search(keywords, word):
        for keyword in keywords:
            if keyword.lower() in word.lower():
                return True
        return False

    def emit_batch(self, results):
        if not self.canceled:
            self.signals.batch_found.emit(results)

    @pyqtSlot()
    def run(self):
        results = []
        try:
            index = Indexer.load_obj(self.index_path)
        except FileNotFoundError:
            print("File Not Found")
        else:
            self.signals.started.emit()
            for i in range(len(index)):
                if self.canceled:
                    break
                if len(results) >= self.batch_amount:
                    self.emit_batch(results)
                    results.clear()
                if index[i].search(self.keywords, self.excluded_words):
                    print(index[i].title)
                    results.append(index[i])
            if len(results) > 0:
                self.emit_batch(results)
        self.signals.finished.emit()

    def cancel(self):
        self.canceled = True
