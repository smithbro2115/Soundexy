from PyQt5.QtCore import QMimeData
from PyQt5.QtWidgets import QMessageBox, QStyledItemDelegate
import qdarkstyle


class InternalMoveMimeData(QMimeData):
    def __init__(self):
        super(InternalMoveMimeData, self).__init__()
        self.result = None


def show_are_you_sure(msg):
    dialog = QMessageBox()
    dialog.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    dialog.setText(msg)
    dialog.setWindowTitle('Are You Sure?')
    dialog.setStandardButtons(dialog.No | dialog.Yes)
    dialog.setDefaultButton(dialog.Yes)
    return dialog.exec_() == dialog.Yes


def show_error(msg):
    error = QMessageBox()
    error.setWindowTitle('Error')
    error.setText(msg)
    error.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    error.exec_()


class PlaylistItemDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        super(PlaylistItemDelegate, self).__init__(parent)

    def setModelData(self, QWidget, QAbstractItemModel, QModelIndex):
        item = self.parent().itemFromIndex(QModelIndex)
        try:
            self.parent().make_or_rename_playlist(item, QWidget.text())
            super(PlaylistItemDelegate, self).setModelData(QWidget, QAbstractItemModel, QModelIndex)
        except FileExistsError as e:
            show_error(str(e))
            self.parent().edit_item(item, QModelIndex)
