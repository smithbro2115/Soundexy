from PyQt5.QtCore import QMimeData
from PyQt5.QtWidgets import QErrorMessage, QTr
from PyQt5.QtGui import QStandardItemModel


class InternalMoveMimeData(QMimeData):
    pass


def show_error(msg):
    error = QErrorMessage()
    error.showMessage('Error', msg)


def setup_playlist_tree(tree):
    model = QStandardItemModel()
    model.setColumnCount(2)
    model.setHorizontalHeaderLabels(['Name', 'Index'])
    model.appendRow(make_row('Test Playlist', 'Newest'))
    tree.setModel(model)


def make_row(name, index):
    name_item = QStandardItem(name)
    index_item = QStandardItem(index)
    return [name_item, index_item]
