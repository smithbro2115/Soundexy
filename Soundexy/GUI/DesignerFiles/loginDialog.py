# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\Josh\PycharmProjects\Soundexy\loginDialog.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_login(object):
    def setupUi(self, login):
        login.setObjectName("login")
        login.resize(400, 169)
        self.gridLayout = QtWidgets.QGridLayout(login)
        self.gridLayout.setObjectName("gridLayout")
        self.label_2 = QtWidgets.QLabel(login)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)
        self.userLineEdit = QtWidgets.QLineEdit(login)
        self.userLineEdit.setObjectName("userLineEdit")
        self.gridLayout.addWidget(self.userLineEdit, 1, 1, 1, 1)
        self.passwordLineEdit = QtWidgets.QLineEdit(login)
        self.passwordLineEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.passwordLineEdit.setObjectName("passwordLineEdit")
        self.gridLayout.addWidget(self.passwordLineEdit, 2, 1, 1, 1)
        self.loginSiteName = QtWidgets.QLabel(login)
        font = QtGui.QFont()
        font.setPointSize(15)
        font.setBold(True)
        font.setWeight(75)
        self.loginSiteName.setFont(font)
        self.loginSiteName.setAlignment(QtCore.Qt.AlignCenter)
        self.loginSiteName.setObjectName("loginSiteName")
        self.gridLayout.addWidget(self.loginSiteName, 0, 0, 1, 2)
        self.buttonBox = QtWidgets.QDialogButtonBox(login)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 8, 0, 1, 2)
        self.label = QtWidgets.QLabel(login)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)
        self.rememberCheckBox = QtWidgets.QCheckBox(login)
        self.rememberCheckBox.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.rememberCheckBox.setObjectName("rememberCheckBox")
        self.gridLayout.addWidget(self.rememberCheckBox, 3, 1, 1, 1)

        self.retranslateUi(login)
        self.buttonBox.accepted.connect(login.accept)
        self.buttonBox.rejected.connect(login.reject)
        QtCore.QMetaObject.connectSlotsByName(login)

    def retranslateUi(self, login):
        _translate = QtCore.QCoreApplication.translate
        login.setWindowTitle(_translate("login", "Login"))
        self.label_2.setText(_translate("login", "Password:"))
        self.loginSiteName.setText(_translate("login", "Login into "))
        self.label.setText(_translate("login", "Username:"))
        self.rememberCheckBox.setText(_translate("login", "Remember me"))

