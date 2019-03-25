from PyQt5 import QtWidgets


li = []
button = QtWidgets.QPushButton()
li.append(button)
print(li)
button = None
print(li)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = Gui()
    MainWindow = Window(ui)
    ui.setupUi(MainWindow)
    ui.setup_ui_additional(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())