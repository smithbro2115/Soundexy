# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Programming\Soundexy\DownloadButton.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(276, 24)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setMinimumSize(QtCore.QSize(0, 24))
        self.downloadButton = QtWidgets.QPushButton(Form)
        self.downloadButton.setGeometry(QtCore.QRect(0, 0, 270, 23))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.downloadButton.sizePolicy().hasHeightForWidth())
        self.downloadButton.setSizePolicy(sizePolicy)
        self.downloadButton.setMinimumSize(QtCore.QSize(0, 23))
        self.downloadButton.setStyleSheet("background-color: #00ffff00")
        self.downloadButton.setObjectName("downloadButton")
        self.downloadProgressBar = QtWidgets.QProgressBar(Form)
        self.downloadProgressBar.setGeometry(QtCore.QRect(0, 0, 270, 23))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.downloadProgressBar.sizePolicy().hasHeightForWidth())
        self.downloadProgressBar.setSizePolicy(sizePolicy)
        self.downloadProgressBar.setMinimumSize(QtCore.QSize(0, 23))
        self.downloadProgressBar.setStyleSheet("")
        self.downloadProgressBar.setProperty("value", 0)
        self.downloadProgressBar.setTextVisible(False)
        self.downloadProgressBar.setObjectName("downloadProgressBar")
        self.downloadProgressBar.raise_()
        self.downloadButton.raise_()

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.downloadButton.setText(_translate("Form", "Download"))

