from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal
import traceback
import DownloadButton


class SearchResultSignals(QtCore.QObject):
    drop_sig = pyqtSignal(list)
    meta_edit = pyqtSignal(dict)


class SelectiveReadOnlyColumnModel(QtGui.QStandardItemModel):
    def __init__(self, table_view):
        super(SelectiveReadOnlyColumnModel, self).__init__()
        self.read_only_columns = []
        self.current_results = {}
        self.table_view = table_view

    def set_read_only_columns(self, column_indexes):
        self.read_only_columns = column_indexes

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
                result.set_tag(k, v)
                return True
            except Exception as e:
                traceback.print_exc()
                return False

    def get_id_from_row(self, row_number: int) -> str:
        return self.index(row_number, self.table_view.get_column_index('id')).data()


class DownloadButtonLocal(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(DownloadButtonLocal, self).__init__(parent=parent)
        self.ui = DownloadButton.Ui_Form()
        self.ui.setupUi(self)


class SearchResultsTable(QtWidgets.QTableView):
    def __init__(self):
        super(SearchResultsTable, self).__init__()
        self.row_order = {'File Name': 0, 'Title': 1, 'Description': 2, 'Duration': 3,
                          'Library': 4, 'Artist': 5, 'Id': 6}
        self.setAcceptDrops(True)
        self.searchResultsTableModel = SelectiveReadOnlyColumnModel(self)
        self.searchResultsTableModel.set_read_only_columns([self.get_column_index('Duration'),
                                                            self.get_column_index('Library'),
                                                            self.get_column_index('Id')])
        self.setModel(self.searchResultsTableModel)
        self.headers = sorted(self.row_order, key=self.row_order.get)
        self.searchResultsTableModel.headers = self.headers
        self.searchResultsTableModel.setHorizontalHeaderLabels(self.searchResultsTableModel.headers)
        self.searchResultsTableModel.setColumnCount(7)
        self.current_results = {}
        self.signals = SearchResultSignals()
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSortingEnabled(True)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers | QtWidgets.QAbstractItemView.SelectedClicked)
        self.verticalHeader().setVisible(False)
        self.setColumnHidden(self.get_column_index('id'), True)

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

    @staticmethod
    def special_values(k, v):
        if k == 'duration':
            duration = v / 1000
            minutes = duration // 60
            seconds = duration % 60
            return '%02d:%02d' % (minutes, seconds)
        else:
            return v

    def add_results_to_search_results_table(self, results):
        for result in results:
            self.current_results[result.id] = result

            meta_file = result.meta_file
            standard_items = {}
            for k, v in meta_file().items():
                if isinstance(v, list):
                    readable_version = self.convert_none_into_space(v[0])
                else:
                    readable_version = self.convert_none_into_space(v)
                checked_for_special = self.special_values(k, readable_version)
                item = QtGui.QStandardItem(str(checked_for_special))
                standard_items[k] = item
            standard_items['Id'] = QtGui.QStandardItem(str(result.id))
            self.add_to_table_model(standard_items)
            self.sort()

    def sort(self):
        self.sortByColumn(self.horizontalHeader().sortIndicatorSection(),
                          self.horizontalHeader().sortIndicatorOrder())

    def return_empty_row(self):
        row = []
        for i in range(0, self.searchResultsTableModel.columnCount(), 1):
            row.append(QtGui.QStandardItem(''))
        return row

    def add_to_table_model(self, meta_dict):
        row = self.return_empty_row()
        for k, v in meta_dict.items():
            index = self.get_column_index(k)
            if index >= 0:
                row[index] = v
            else:
                self.add_new_column(k)
                row.append(v)
        self.searchResultsTableModel.appendRow(row)

    def get_column_index(self, header):
        header_count = self.searchResultsTableModel.columnCount()
        for x in range(0, header_count, 1):
            header_text = self.searchResultsTableModel.horizontalHeaderItem(x).text().lower()
            if header_text == header.lower():
                return x
        else:
            return -1

    def add_new_column(self, header, hidden=True):
        self.row_order[header.title()] = len(self.row_order.keys())
        self.headers = sorted(self.row_order, key=self.row_order.get)
        self.searchResultsTableModel.setColumnCount(self.searchResultsTableModel.columnCount())
        self.searchResultsTableModel.setHorizontalHeaderLabels(self.headers)
        if hidden:
            self.setColumnHidden(self.searchResultsTableModel.columnCount() - 1, True)

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

