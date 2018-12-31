from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal


# TODO Make sure added results get added in the right order when they are sorted (this may take some time)


class SearchResultSignals(QtCore.QObject):
    drop_sig = pyqtSignal(str)


class SearchResultsTable(QtWidgets.QTableView):
    def __init__(self):
        super(SearchResultsTable, self).__init__()
        self.row_order = {'Title': 0, 'Description': 1, 'Duration': 2,
                          'Library': 3, 'Author': 4, 'Id': 5}
        self.setAcceptDrops(True)
        self.searchResultsTableModel = QtGui.QStandardItemModel()
        self.setModel(self.searchResultsTableModel)
        headers = sorted(self.row_order, key=self.row_order.get)
        self.searchResultsTableModel.headers = headers
        self.searchResultsTableModel.setHorizontalHeaderLabels(self.searchResultsTableModel.headers)
        self.searchResultsTableModel.setColumnCount(6)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.current_results = {}
        self.signals = SearchResultSignals()
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSortingEnabled(True)
        self.verticalHeader().setVisible(False)

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
