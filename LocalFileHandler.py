import os
import pickle
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QRunnable, QThreadPool
from SearchResults import Local


excepted_file_types = ['.mp3', '.wav', '.flac', '.ogg']


def load_obj(name):
    with open('obj/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)


def save_obj(obj, name):
    with open('obj/' + name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def add_to_index(path):
    index = []
    try:
        index = load_obj('local_index')
        for i in index:
            print(i.title)
    except FileNotFoundError:
        save_obj(index, 'local_index')
        print('Made New Index File')
    finally:
        index_paths = []
        for i in index:
            index_paths.append(i.path)
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file.title())
                    if determine_if_file_should_be_added_to_index(file_path, index_paths):
                        append_to_index(index, file_path)
                save_obj(index, 'local_index')
        else:
            if determine_if_file_should_be_added_to_index(path, index_paths):
                append_to_index(index, path)
                save_obj(index, 'local_index')


def append_to_index(index, file_path):
    i = 'L%08d' % len(index)
    local_result = Local()
    local_result.populate(file_path, i)
    index.append(local_result)
    print('Added: ' + file_path + ' to local_index')


def determine_if_file_should_be_added_to_index(file_path, index_paths):
    extension = os.path.splitext(file_path)[1]
    if extension.lower() in excepted_file_types:
        if file_path not in index_paths:
            return True
        else:
            return False


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

    @staticmethod
    def search(keywords, word):
        for keyword in keywords:
            if keyword.lower() in word.lower():
                return True
        return False

    @pyqtSlot()
    def run(self):
        results = []
        try:
            index = load_obj(self.index_path)
        except FileNotFoundError:
            print("File Not Found")
        else:
            self.signals.started.emit()
            for i in range(len(index)):
                if len(results) >= self.batch_amount:
                    self.signals.batch_found.emit(results)
                    results.clear()
                if index[i].search(self.keywords, self.excluded_words):
                    print(index[i].title)
                    results.append(index[i])
            if len(results) > 0:
                self.signals.batch_found.emit(results)
        self.signals.finished.emit()
