import osimport timefrom PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QRunnable, QThreadPoolfrom Soundexy.Functionality.useful_utils import get_app_data_folder, make_folder_if_it_does_not_existfrom Soundexy.Indexing import Indexingfrom Soundexy.Indexing import SearchResultsclass IndexerSigs(QObject):    started_adding_items = pyqtSignal()    added_item = pyqtSignal(str)    finished_adding_items = pyqtSignal()    deleted_item = pyqtSignal(str)    error = pyqtSignal(str)class Indexer(QRunnable):    def __init__(self):        super(Indexer, self).__init__()        self.index_file_name = 'local_index'        self.signals = IndexerSigs()        self.paths = []        self.emitted_start_adding_items = False    @staticmethod    def emit_signal_if_condition_false(signal: pyqtSignal, condition: bool):        if not condition:            signal.emit()            return True        else:            return False    def emit_started_adding_items(self, index):        if self.emit_signal_if_condition_false(self.signals.started_adding_items, self.emitted_start_adding_items):            index.signals.added_item.connect(lambda x: self.signals.added_item.emit(x))            self.emitted_start_adding_items = True    def run(self):        self.reset()        index = IndexFile(self.index_file_name, 'obj')        if len(self.paths) > 1:            self.add_multiple_paths_to_index(self.paths, index)        else:            self.add_path_to_index(self.paths[0], index)        if self.emitted_start_adding_items:            self.signals.finished_adding_items.emit()    def reset(self):        self.emitted_start_adding_items = False    def add_multiple_paths_to_index(self, paths, index):        self.emit_started_adding_items(index)        for path in paths:            self.add_path_to_index(path, index)        self.signals.finished_adding_items.emit()    def add_path_to_index(self, path, index):        if os.path.isdir(path):            self.emit_started_adding_items(index)            index.add_dir_to_index(path)        else:            index.add_single_to_index(path)        index.save()class IndexFileSigs(QObject):    error = pyqtSignal(str)    added_item = pyqtSignal(str)    deleted_item = pyqtSignal(str)time_to_make_numbs = []class IndexFile:    def __init__(self, file_name, app_data_folder, schema):        self.index_file_name = file_name        self.signals = IndexFileSigs()        self.schema = schema        self.emitted_start_adding_items = False        self.excepted_file_types = ['.mp3', '.wav', '.flac', '.ogg']        self.index = None        self.app_data_folder = app_data_folder        self.writer = None        self.load()        self.counter = 0    def determine_if_file_should_be_added_to_index(self, file_path):        extension = os.path.splitext(file_path)[1]        if extension.lower() in self.excepted_file_types:            return True    def add_dir_to_index(self, path):        for root, dirs, files in os.walk(path):            for file in files:                start_time = time.time()                file_path = os.path.join(root, file.title())                self.add_single_to_index(file_path)                time_to_make_numbs.append(time.time() - start_time)    def add_single_to_index(self, path):        if self.determine_if_file_should_be_added_to_index(path):            try:                start_time = time.time()                print(f"It took: {time.time() - start_time} to make this result")                self.append_result_to_index(Indexing.make_document(path))                self.signals.added_item.emit(path)                self.counter += 1                # if self.counter >= 1000:                #     self.counter = 0                #     self.save()            except (AttributeError, Indexing.w_writing.IndexingError):                self.writer = self.index.writer()                self.add_single_to_index(path)    def add_result_to_index(self, result):        self.append_result_to_index(result)    def make_result(self, index, file_path):        first_letter = self.index_file_name[0].upper()        # i = first_letter + '%08d' % len(index)        # if local_result.populate(file_path, i):        #     return local_result    def append_result_to_index(self, result):        Indexing.write_to_index(self.writer, **result)    def changed_meta_data(self, result):        self.delete_from_index(result)        self.append_result_to_index(result)        self.save()    def delete_from_index(self, result):        try:            self.index = self.load_obj(self.index_file_name)        except FileNotFoundError as e:            self.signals.error.emit(e)        else:            try:                self.index.pop(self.index.index(result))                self.save()            except KeyError as e:                self.signals.error.emit(e)    def save(self):        self.writer.commit()    def load(self):        path = make_folder_if_it_does_not_exist(self.app_data_folder, self.index_file_name)        try:            self.index = Indexing.open_index(path)        except Indexing.w_index.EmptyIndexError:            self.index = Indexing.create_index(path, self.schema)            print('Made New Index File Named: ' + self.index_file_name)class LocalSearchSigs(QObject):    started = pyqtSignal()    batch_found = pyqtSignal(Indexing.ResultsPage)    updated_results = pyqtSignal(Indexing.ResultsPage)    finished = pyqtSignal()class IndexSearch(QRunnable):    def __init__(self, search_text, index_app_data=get_app_data_folder("index"), index_name="local", batch_amount=50,                 sort_by=""):        super(IndexSearch, self).__init__()        self.search_text = search_text        self.signals = LocalSearchSigs()        self.index_path = index_app_data        self.index_name = index_name        self.batch_amount = batch_amount        self.sort_by = sort_by        self.canceled = False    def emit_batch(self, results):        if not self.canceled:            self.signals.batch_found.emit(results)    def update_results(self, results):        if not self.canceled:            self.signals.updated_results.emit(results)    @pyqtSlot()    def run(self):        try:            index = IndexFile(self.index_name, self.index_path, Indexing.ResultSchema()).index        except FileNotFoundError:            print("File Not Found")        else:            self.signals.started.emit()            query = Indexing.construct_query(index, self.search_text)            for page in Indexing.search_page(index, query, sort_by=self.sort_by):                if self.canceled:                    break                self.emit_batch(self.make_results_from_hits(list(page)))        self.signals.finished.emit()    def cancel(self):        self.canceled = True