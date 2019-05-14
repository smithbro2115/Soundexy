from PyQt5.QtCore import QMimeData, Qt
from PyQt5.QtWidgets import QMessageBox, QTreeWidgetItem, QStyledItemDelegate
import qdarkstyle
from Soundexy.Functionality import Playlists


class InternalMoveMimeData(QMimeData):
    pass


def show_error(msg):
    error = QMessageBox()
    error.setWindowTitle('Error')
    error.setText(msg)
    error.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    error.exec_()


def add_root_to_tree(parent, row):
    name_item = PlaylistTreeWidgetItem(parent, row)
    name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
    return name_item


def add_to_tree_object(parent, row):
    name_item = QTreeWidgetItem(parent, row)
    return name_item


def make_playlist(tree):
    playlist_item = add_root_to_tree(tree, ['Playlist name'])
    tree.setFocus()
    tree.editItem(playlist_item)


class PlaylistTreeWidgetItem(QTreeWidgetItem):
    def __init__(self, parent, row):
        super(PlaylistTreeWidgetItem, self).__init__(parent, row)
        self.last_text = None

    def setData(self, p_int, p_int_1, Any):
        super(PlaylistTreeWidgetItem, self).setData(p_int, p_int_1, Any)
        self.last_text = self.text(0)
        print('set last text', self.last_text)


class PlaylistItemDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        super(PlaylistItemDelegate, self).__init__(parent)

    def setModelData(self, QWidget, QAbstractItemModel, QModelIndex):
        item = self.parent().itemFromIndex(QModelIndex)
        try:
            self.make_or_rename_playlist(item, QWidget.text())
            super(PlaylistItemDelegate, self).setModelData(QWidget, QAbstractItemModel, QModelIndex)
        except FileExistsError as e:
            show_error(str(e))
            self.parent().edit_item(item, QModelIndex)

    def make_or_rename_playlist(self, item, text):
        if item.last_text is None:
            self.make_playlist_index_from_string(text)
        else:
            self.rename_playlist_from_item(item, text)

    def rename_playlist_from_item(self, item, text):
        Playlists.rename_playlist_index(text, item.last_text)

    def make_playlist_index_from_string(self, text):
        Playlists.make_playlist_index(text)
