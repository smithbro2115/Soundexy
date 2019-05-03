from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal
import traceback
from Soundexy.Functionality.useful_utils import get_formatted_duration_from_milliseconds, get_yes_no_from_bool
import os
from Soundexy.GUI.API.CustomPyQtFunctionality import InternalMoveMimeData
from Soundexy.GUI.API import pyqt_utils
from Soundexy.GUI.DesignerFiles import loginDialog
import qdarkstyle


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

    def get_row_from_id(self, id_number):
        for row_number in range(self.rowCount()):
            if self.get_id_from_row(row_number) == id_number:
                return row_number


class RemoveButtonSigs(QtCore.QObject):
    hover = pyqtSignal()
    unhover = pyqtSignal()


class DownloadButtonRemove(QtWidgets.QPushButton):
    def __init__(self):
        self.signals = RemoveButtonSigs()
        super(DownloadButtonRemove, self).__init__()
        font = QtGui.QFont("Segoe UI Symbol")
        self.setFont(font)

    def enterEvent(self, *args, **kwargs):
        self.signals.hover.emit()
        super(DownloadButtonRemove, self).enterEvent(*args, **kwargs)

    def leaveEvent(self, *args, **kwargs):
        self.signals.unhover.emit()
        super(DownloadButtonRemove, self).leaveEvent(*args, **kwargs)


class DownloadButtonSigs(QtCore.QObject):
    delete = pyqtSignal()
    cancel = pyqtSignal()


class DownloadButtonLocal(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(DownloadButtonLocal, self).__init__(parent=parent)
        self.current_result = None
        self.signals = DownloadButtonSigs()
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        # layout.setStretch(5, 5)
        self.setLayout(layout)
        self.progress_bar = QtWidgets.QProgressBar()
        self.layout().addWidget(self.progress_bar)
        self.delete_button = DownloadButtonRemove()
        self.delete_button.setMinimumWidth(27)
        self.delete_button.setText(' X ')
        self.delete_button.setStyleSheet('background-color: #00ffff00')
        self.layout().addWidget(self.delete_button)
        self.delete_button.setHidden(True)
        self.button = QtWidgets.QPushButton()
        self.button.setText('Download')
        self.button.setStyleSheet('background-color: #00ffff00')
        self.button.setFocusPolicy(QtCore.Qt.NoFocus)
        progress_layout = QtWidgets.QHBoxLayout()
        progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_bar.setLayout(progress_layout)
        self.progress_bar.setTextVisible(False)
        self.animation = None
        self.progress_bar.layout().addWidget(self.button)

    def downloaded_started(self):
        self.button.setText('Downloading')
        self.button.setEnabled(False)
        self.delete_button.setHidden(False)
        self.remove_button_downloading_mode()

    def done(self):
        self.progress_bar.setValue(100)
        self.button.setEnabled(False)
        self.button.setText('Downloaded')
        self.delete_button.setHidden(False)
        self.remove_button_downloaded_mode()

    def remove_button_downloaded_mode(self):
        self.delete_button.setText(' ✓ ')
        self.delete_button.signals.hover.connect(lambda: self.delete_button.setText(' X '))
        self.delete_button.signals.unhover.connect(lambda: self.delete_button.setText(' ✓ '))
        pyqt_utils.disconnect_all_signals(self.delete_button.clicked)
        self.delete_button.clicked.connect(lambda: self.signals.delete.emit())

    def remove_button_downloading_mode(self):
        pyqt_utils.disconnect_all_signals(self.delete_button.signals.hover, self.delete_button.signals.unhover,
                                          self.delete_button.clicked)
        self.delete_button.clicked.connect(lambda: self.signals.cancel.emit())

    def reset(self):
        self.progress_bar.setValue(0)
        self.button.setEnabled(True)
        self.delete_button.setHidden(True)
        self.button.setText('Download')
        self.delete_button.setText(' X ')

    def set_delete_button_function(self, function):
        pyqt_utils.disconnect_all_signals(self.delete_button.clicked)
        self.delete_button.clicked.connect(function)

    def set_button_function(self, function):
        pyqt_utils.disconnect_all_signals(self.button.clicked)
        self.button.clicked.connect(function)

    def set_progress(self, value: int):
        self.smooth_progress_bar_change(value)

    def smooth_progress_bar_change(self, value):
        self.animation = QtCore.QPropertyAnimation(self.progress_bar, b"value")
        self.animation.setDuration(1500)
        self.animation.setStartValue(self.progress_bar.value())
        self.animation.setEndValue(value)
        self.animation.start()


class SearchResultTableHeaderContextMenu(QtWidgets.QMenu):
    def __init__(self, parent):
        super(SearchResultTableHeaderContextMenu, self).__init__(parent)
        self.model = parent.searchResultsTableModel
        self.main = parent
        self.make_actions()

    def make_actions(self):
        for header_index in range(self.model.columnCount()):
            is_visible = not self.main.isColumnHidden(header_index)
            action = self.addAction(self.main.headers[header_index])
            action.setCheckable(True)
            action.setChecked(is_visible)
            action.setData(header_index)


class SearchResultsTable(QtWidgets.QTableView):
    def __init__(self):
        super(SearchResultsTable, self).__init__()
        self.row_order = {'File Name': 0, 'Title': 1, 'Description': 2, 'Duration': 3,
                          'Library': 4, 'Author': 5, 'Id': 6, 'Available Locally': 7}
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.searchResultsTableModel = SelectiveReadOnlyColumnModel(self)
        self.searchResultsTableModel.set_read_only_columns([self.get_column_index('Duration'),
                                                            self.get_column_index('Library'),
                                                            self.get_column_index('Available Locally'),
                                                            self.get_column_index('Id')])
        self.setModel(self.searchResultsTableModel)
        self.headers = sorted(self.row_order, key=self.row_order.get)
        self.searchResultsTableModel.headers = self.headers
        self.searchResultsTableModel.setHorizontalHeaderLabels(self.searchResultsTableModel.headers)
        self.searchResultsTableModel.setColumnCount(8)
        self.current_results = {}
        self.horizontalHeader().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(self.show_context_menu)
        self.signals = SearchResultSignals()
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSortingEnabled(True)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers | QtWidgets.QAbstractItemView.SelectedClicked)
        self.horizontalHeader().setSectionsMovable(True)
        self.verticalHeader().setVisible(False)
        self.setColumnHidden(self.get_column_index('id'), True)

    def show_context_menu(self, event):
        context = SearchResultTableHeaderContextMenu(self)
        action = context.exec_(self.mapToGlobal(event))
        if action:
            self.header_context_menu_clicked(action)

    def header_context_menu_clicked(self, action):
        checked = action.isChecked()
        header_index = action.data()
        self.setColumnHidden(header_index, not checked)

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
            return get_formatted_duration_from_milliseconds(v)
        elif k == 'available locally':
            return get_yes_no_from_bool(v)
        else:
            return v

    def add_results_to_search_results_table(self, results):
        for result in results:
            self.current_results[result.id] = result
            standard_items = self.make_standard_items_from_result(result)
            self.append_row(self.make_row(standard_items))
            self.sort()

    def make_standard_items_from_result(self, result):
        meta_file = result.meta_file
        standard_items = {}
        for k, v in meta_file().items():
            if isinstance(v, list):
                readable_version = self.convert_none_into_space(', '.join(v))
            else:
                readable_version = self.convert_none_into_space(v)
            checked_for_special = self.special_values(k, readable_version)
            item = QtGui.QStandardItem(str(checked_for_special))
            standard_items[k] = item
        standard_items['Id'] = QtGui.QStandardItem(str(result.id))
        standard_items['Available Locally'] = QtGui.QStandardItem(self.special_values('available locally',
                                                                                      result.available_locally))
        return standard_items

    def replace_result(self, new_result, old_result):
        current_index = self.currentIndex()
        index = self.searchResultsTableModel.get_row_from_id(old_result.id)
        new_row = self.make_row(self.make_standard_items_from_result(new_result))
        self.current_results[old_result.id] = None
        self.current_results[new_result.id] = new_result
        try:
            self.replace_row(new_row, index)
            self.setCurrentIndex(current_index)
        except TypeError:
            pass

    def append_row(self, row):
        self.searchResultsTableModel.appendRow(row)

    def add_row_at(self, row, index):
        self.searchResultsTableModel.insertRow(index, row)

    def replace_row(self, new_row_item, old_row_number):
        self.delete_row(old_row_number)
        self.add_row_at(new_row_item, old_row_number)

    def delete_row(self, row_number):
        self.searchResultsTableModel.takeRow(row_number)

    def sort(self):
        self.sortByColumn(self.horizontalHeader().sortIndicatorSection(),
                          self.horizontalHeader().sortIndicatorOrder())

    def return_empty_row(self):
        row = []
        for i in range(0, self.searchResultsTableModel.columnCount(), 1):
            row.append(QtGui.QStandardItem(''))
        return row

    def make_row(self, meta_dict, index=-1):
        row = self.return_empty_row()
        for k, v in meta_dict.items():
            index = self.get_column_index(k)
            if index >= 0:
                row[index] = v
            else:
                new_index = self.add_new_column(k)
                row.insert(new_index, v)
        return row

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
        new_index = self.searchResultsTableModel.columnCount()
        if hidden:
            self.setColumnHidden(new_index - 1, True)
        return new_index

    def get_mime_data(self):
        result = self.current_results[self.searchResultsTableModel.get_id_from_row(self.currentIndex().row())]
        data = InternalMoveMimeData()
        if result.available_locally:
            path = os.path.abspath(result.path)
            data.setUrls([QtCore.QUrl.fromLocalFile(path)])
        return data

    def startDrag(self, *args, **kwargs):
        a = QtGui.QDrag(self)
        data = self.get_mime_data()
        a.setMimeData(data)
        a.exec_(QtCore.Qt.CopyAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and not isinstance(event.mimeData(), InternalMoveMimeData):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls and not isinstance(event.mimeData(), InternalMoveMimeData):
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


class LoginDialogSigs(QtCore.QObject):
    accepted = pyqtSignal(tuple)
    canceled = pyqtSignal()


class LoginDialog(QtWidgets.QDialog):
    def __init__(self, website, parent=None):
        super(LoginDialog, self).__init__(parent)
        self.signals = LoginDialogSigs()
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.ui = loginDialog.Ui_login()
        self.ui.setupUi(self)
        self.ui.loginSiteName.setText(f'Login into {website}')