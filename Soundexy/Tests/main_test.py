from Soundexy.Indexing.LocalFileHandler import IndexSearch
from Soundexy.GUI.DesignerFiles.Test import Ui_MainWindow
from Soundexy.GUI.API.CustomPyQtWidgets import SearchResultsTable, SearchResultsItemModel, \
    make_standard_items_from_results, SelectiveReadOnlyColumnModel
from PyQt5.QtCore import QThreadPool, QRunnable
from PyQt5 import QtWidgets, QtGui, QtCore
from whoosh.searching import Hit
from Soundexy.Indexing import SearchResults
import traceback


class Gui(Ui_MainWindow):
    def __init__(self):
        self.thread_pool = QThreadPool()
        self.search = None
        self.tableView = SearchResultsTable(self)
        self.empty_model = None

    def setup_additional(self):
        self.empty_model = SearchResultsItemModel([], self.tableView)
        self.centralwidget.layout().addWidget(self.tableView, 2, 0)
        self.pushButton.clicked.connect(self.clear_table)
        self.searchPushButton.clicked.connect(self.run)

    def clear_table(self):
        self.tableView.go_to_empty_model()

    def run(self):
        self.search = Search("-gun", self.tableView)
        self.search.signals.finished.connect(self.search_finished)
        self.search.signals.started.connect(self.search_finished)
        self.thread_pool.start(self.search)

    def search_finished(self, model):
        self.tableView.setModel(model)

    def process_hit(self, hit: Hit):
        title_item = QtGui.QStandardItem(hit.get('file_name'))
        path_item = QtGui.QStandardItem(hit.get('path'))
        row = self.tableView.model().rowCount()
        self.tableView.model().setRowCount(row+1)
        self.tableView.model().setItem(row, 0, title_item)
        self.tableView.model().setItem(row, 1, path_item)


class SearchSignals(QtCore.QObject):
    started = QtCore.pyqtSignal(QtCore.QAbstractItemModel)
    finished = QtCore.pyqtSignal(QtCore.QAbstractItemModel)
    batch = QtCore.pyqtSignal(list)


class Search(QRunnable):
    def __init__(self, query, table: SearchResultsTable):
        super(Search, self).__init__()
        self.thread_pool = QThreadPool()
        self.signals = SearchSignals()
        self.model = SearchResultsItemModel([], table)
        self.sort_model = QtCore.QSortFilterProxyModel()
        self.sort_model.setSourceModel(self.model)
        sort_column = self.model.columns[table.horizontalHeader().sortIndicatorSection()]
        sort_reverse = table.horizontalHeader().sortIndicatorOrder()
        print(sort_column, bool(sort_reverse))
        self.search = IndexSearch(query, sort_by=sort_column, sort_reverse=sort_reverse)
        self.table = table
        self.counter = 0
        self.done = False

    def run(self):
        self.search.signals.batch_found.connect(self.add_to_model)
        self.search.signals.finished.connect(self.finished)
        self.signals.started.emit(self.sort_model)
        self.search.run()
        while not self.done:
            pass

    def finished(self):
        self.done = True
        # self.signals.finished.emit(self.model)

    def add_to_model(self, batch):
        print("started")
        results = self.make_results_from_hits(batch)
        print(len(results))
        self.model.insertRows(self.model.rowCount(), len(results), rows=results)
        # self.signals.batch.emit(results)
        self.counter += 1
        print(self.model.rowCount())

    def make_row(self, items):
        return items.values()

    def process_hit(self, hit: Hit):
        # title_item = QtGui.QStandardItem(hit.get('file_name'))
        # path_item = QtGui.QStandardItem(hit.get('path'))
        # row = self.model.rowCount()
        # self.model.setRowCount(row + 1)
        row = [QtGui.QStandardItem(hit.get('file_name')), QtGui.QStandardItem(hit.get('path'))]
        # self.model.setItem(row, 0, title_item)
        # self.model.setItem(row, 1, path_item)
        return row

    @staticmethod
    def make_results_from_hits(hits):
        results = []
        for hit in hits:
            try:
                results.append(SearchResults.Local(hit))
            except KeyError:
                pass
        return results


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = Gui()
    MainWindow = QtWidgets.QMainWindow()
    ui.setupUi(MainWindow)
    ui.setup_additional()
    MainWindow.show()
    sys.exit(app.exec_())
