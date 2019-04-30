from PyQt5.QtCore import QMimeData
from PyQt5.QtWidgets import QErrorMessage


class InternalMoveMimeData(QMimeData):
    pass


def show_error(msg):
    error = QErrorMessage()
    error.showMessage('Error', msg)
