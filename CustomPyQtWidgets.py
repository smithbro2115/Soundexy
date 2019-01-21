from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal


class SearchResultSignals(QtCore.QObject):
    drop_sig = pyqtSignal(list)
    meta_edit = pyqtSignal(dict)


class SelectiveReadOnlyColumnModel(QtGui.QStandardItemModel):
    def __init__(self, table_view, read_only_columns):
        super(SelectiveReadOnlyColumnModel, self).__init__()
        self.read_only_columns = read_only_columns
        self.current_results = {}
        self.table_view = table_view

    def flags(self, QModelIndex):
        base_flags = QtGui.QStandardItemModel.flags(self, QModelIndex)
        if QModelIndex.column() in self.read_only_columns:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return base_flags

    def setData(self, QModelIndex, Any, role=None):
        row_id = self.get_id_from_row(QModelIndex.row())
        meta_label = self.horizontalHeaderItem(QModelIndex.column()).text().lower()
        if self.change_result_meta(self.table_view.current_results[row_id], {meta_label: Any}):
            super(SelectiveReadOnlyColumnModel, self).setData(QModelIndex, Any, role)
            return True
        else:
            return False

    @staticmethod
    def change_result_meta(result, meta: dict):
        for k, v in meta.items():
            try:
                result.meta_file.set_tag(k, v)
                result.repopulate()
                return True
            except Exception as e:
                print(e)
                return False

    def get_id_from_row(self, row_number: int) -> str:
        return self.index(row_number, self.table_view.row_order['Id']).data()


class SearchResultsTable(QtWidgets.QTableView):
    def __init__(self):
        super(SearchResultsTable, self).__init__()
        self.row_order = {'Name': 0, 'Title': 1, 'Description': 2, 'Duration': 3,
                          'Library': 4, 'Author': 5, 'Id': 6}
        self.setAcceptDrops(True)
        self.searchResultsTableModel = SelectiveReadOnlyColumnModel(self,
                                                                    [self.row_order['Duration'],
                                                                     self.row_order['Library'],
                                                                     self.row_order['Id']])
        self.setModel(self.searchResultsTableModel)
        headers = sorted(self.row_order, key=self.row_order.get)
        self.searchResultsTableModel.headers = headers
        self.searchResultsTableModel.setHorizontalHeaderLabels(self.searchResultsTableModel.headers)
        self.searchResultsTableModel.setColumnCount(7)
        self.current_results = {}
        self.signals = SearchResultSignals()
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSortingEnabled(True)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers | QtWidgets.QAbstractItemView.SelectedClicked)
        self.verticalHeader().setVisible(False)

    @staticmethod
    def convert_none_into_space(result):
        if result is None:
            return ''
        else:
            return result

    @staticmethod
    def try_to_get_value_from_meta_file(value):
        try:
            return value
        except AttributeError:
            return ''

    def add_results_to_search_results_table(self, results):
        for result in results:
            self.current_results[result.id] = result

            meta_file = result.meta_file
            print(meta_file)
            title_cell = QtGui.QStandardItem(str(self.convert_none_into_space(meta_file.title)))
            description_cell = QtGui.QStandardItem(str(self.convert_none_into_space(meta_file.description)))
            duration = meta_file.duration/1000
            minutes = duration // 60
            seconds = duration % 60
            duration_cell = QtGui.QStandardItem('%02d:%02d' % (minutes, seconds))
            author_cell = QtGui.QStandardItem(str(self.convert_none_into_space(meta_file.artist)))
            library_cell = QtGui.QStandardItem(str(self.convert_none_into_space(result.library)))
            sound_id = QtGui.QStandardItem(str(result.id))
            name = QtGui.QStandardItem(str(meta_file.filename))
            row = Row(self.row_order, title_cell, author_cell,
                      description_cell, duration_cell, library_cell, sound_id, name)

            self.searchResultsTableModel.appendRow(row)
            self.sort()

    def sort(self):
        self.sortByColumn(self.horizontalHeader().sortIndicatorSection(),
                          self.horizontalHeader().sortIndicatorOrder())

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.LinkAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        paths = []
        for f in files:
            paths.append(f)
        self.signals.drop_sig.emit(paths)


class Row(list):
    def __init__(self, order, title, author, description, duration, library, id, name):
        super().__init__()
        self.title = title
        self.author = author
        self.description = description
        self.duration = duration
        self.library = library
        self.id = id
        self.name = name
        for key in order:
            self.append_to_self(key, order[key])

    def append_to_self(self, name, index):
        if name == 'Title':
            self.insert(index, self.title)
        elif name == 'Name':
            self.insert(index, self.name)
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
