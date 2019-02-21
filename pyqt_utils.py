from PyQt5.QtCore import pyqtSignal


def disconnect_all_signals(slot):
    try:
        slot.disconnect()
    except TypeError:
        pass
