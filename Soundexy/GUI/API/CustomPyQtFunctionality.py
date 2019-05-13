from PyQt5.QtCore import QMimeData, Qt
from PyQt5.QtWidgets import QMessageBox, QTreeWidgetItem, QTreeWidget
from Soundexy.Functionality import Playlists
import qdarkstyle


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
        self.last_text = self.text(0)
        super(PlaylistTreeWidgetItem, self).setData(p_int, p_int_1, Any)
