# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\Josh\PycharmProjects\Soundexy\DownloadButton.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(278, 24)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setMinimumSize(QtCore.QSize(0, 24))
        self.horizontalLayout = QtWidgets.QHBoxLayout(Form)
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.buttonContainer = QtWidgets.QWidget(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonContainer.sizePolicy().hasHeightForWidth())
        self.buttonContainer.setSizePolicy(sizePolicy)
        self.buttonContainer.setObjectName("buttonContainer")
        self.downloadButton = QtWidgets.QPushButton(self.buttonContainer)
        self.downloadButton.setGeometry(QtCore.QRect(0, 0, 251, 24))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(2)
        sizePolicy.setHeightForWidth(self.downloadButton.sizePolicy().hasHeightForWidth())
        self.downloadButton.setSizePolicy(sizePolicy)
        self.downloadButton.setMinimumSize(QtCore.QSize(0, 0))
        self.downloadButton.setSizeIncrement(QtCore.QSize(0, 0))
        self.downloadButton.setBaseSize(QtCore.QSize(24, 251))
        self.downloadButton.setStyleSheet("background-color: #00ffff00")
        self.downloadButton.setObjectName("downloadButton")
        self.downloadProgressBar = QtWidgets.QProgressBar(self.buttonContainer)
        self.downloadProgressBar.setGeometry(QtCore.QRect(0, 0, 251, 24))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(2)
        sizePolicy.setHeightForWidth(self.downloadProgressBar.sizePolicy().hasHeightForWidth())
        self.downloadProgressBar.setSizePolicy(sizePolicy)
        self.downloadProgressBar.setMinimumSize(QtCore.QSize(0, 0))
        self.downloadProgressBar.setBaseSize(QtCore.QSize(151, 24))
        self.downloadProgressBar.setStyleSheet("")
        self.downloadProgressBar.setProperty("value", 0)
        self.downloadProgressBar.setTextVisible(False)
        self.downloadProgressBar.setObjectName("downloadProgressBar")
        self.downloadProgressBar.raise_()
        self.downloadButton.raise_()
        self.horizontalLayout.addWidget(self.buttonContainer)
        self.deleteButton = QtWidgets.QToolButton(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.deleteButton.sizePolicy().hasHeightForWidth())
        self.deleteButton.setSizePolicy(sizePolicy)
        self.deleteButton.setMinimumSize(QtCore.QSize(24, 24))
        self.deleteButton.setObjectName("deleteButton")
        self.horizontalLayout.addWidget(self.deleteButton)
        self.horizontalLayout.setStretch(0, 5)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.downloadButton.setText(_translate("Form", "Download"))
        self.deleteButton.setText(_translate("Form", "x"))

