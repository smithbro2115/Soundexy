from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal


class SearchResultSignals(QtCore.QObject):
    drop_sig = pyqtSignal(str)
    meta_edit = pyqtSignal(dict)


class SelectiveReadOnlyColumnModel(QtGui.QStandardItemModel):
    def __init__(self, read_only_columns):
        super(SelectiveReadOnlyColumnModel, self).__init__()
        self.read_only_columns = read_only_columns

    def flags(self, QModelIndex):
        base_flags = QtGui.QStandardItemModel.flags(self, QModelIndex)
        if QModelIndex.column() in self.read_only_columns:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return base_flags


class SearchResultsTable(QtWidgets.QTableView):
    def __init__(self):
        super(SearchResultsTable, self).__init__()
        self.row_order = {'Title': 0, 'Description': 1, 'Duration': 2,
                          'Library': 3, 'Author': 4, 'Id': 5}
        self.setAcceptDrops(True)
        self.searchResultsTableModel = SelectiveReadOnlyColumnModel([self.row_order['Duration'],
                                                                     self.row_order['Library'],
                                                                     self.row_order['Id']])
        self.setModel(self.searchResultsTableModel)
        headers = sorted(self.row_order, key=self.row_order.get)
        self.searchResultsTableModel.headers = headers
        self.searchResultsTableModel.setHorizontalHeaderLabels(self.searchResultsTableModel.headers)
        self.searchResultsTableModel.setColumnCount(6)
        self.current_results = {}
        self.signals = SearchResultSignals()
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSortingEnabled(True)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers | QtWidgets.QAbstractItemView.SelectedClicked)
        self.verticalHeader().setVisible(False)

    def closeEditor(self, *args, **kwargs):
        row_id = self.get_id_from_row(self.currentIndex().row())
        meta_label = self.searchResultsTableModel.horizontalHeaderItem(self.currentIndex().column()).text().lower()
        self.signals.meta_edit.emit({row_id: {meta_label: args[0].text()}})
        super().closeEditor(*args, **kwargs)

    @staticmethod
    def convert_none_into_space(result):
        if result is None:
            return ''
        else:
            return result

    def change_result_meta(self, result, meta: dict):
        result.

    def get_id_from_row(self, row_number: int) -> str:
        return self.searchResultsTableModel.index(row_number, self.row_order['Id']).data()

    def add_results_to_search_results_table(self, results):
        for result in results:
            self.current_results[result.id] = result

            title_cell = QtGui.QStandardItem(str(self.convert_none_into_space(result.title)))
            description_cell = QtGui.QStandardItem(str(self.convert_none_into_space(result.description)))
            duration = result.duration/1000
            minutes = duration // 60
            seconds = duration % 60
            duration_cell = QtGui.QStandardItem('%02d:%02d' % (minutes, seconds))
            author_cell = QtGui.QStandardItem(str(self.convert_none_into_space(result.author)))
            library_cell = QtGui.QStandardItem(str(self.convert_none_into_space(result.library)))
            sound_id = QtGui.QStandardItem(str(result.id))
            row = Row(self.row_order, title_cell, author_cell,
                      description_cell, duration_cell, library_cell, sound_id)

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
        for f in files:
            self.signals.drop_sig.emit(f)


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
