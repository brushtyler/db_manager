# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/DlgSqlWindow.ui'
#
# Created: Mon Jun 20 20:07:37 2011
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_DlgSqlWindow(object):
    def setupUi(self, DlgSqlWindow):
        DlgSqlWindow.setObjectName(_fromUtf8("DlgSqlWindow"))
        DlgSqlWindow.resize(385, 471)
        self.vboxlayout = QtGui.QVBoxLayout(DlgSqlWindow)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.label = QtGui.QLabel(DlgSqlWindow)
        self.label.setObjectName(_fromUtf8("label"))
        self.vboxlayout.addWidget(self.label)
        self.editSql = QtGui.QTextEdit(DlgSqlWindow)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.editSql.sizePolicy().hasHeightForWidth())
        self.editSql.setSizePolicy(sizePolicy)
        self.editSql.setObjectName(_fromUtf8("editSql"))
        self.vboxlayout.addWidget(self.editSql)
        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setObjectName(_fromUtf8("hboxlayout"))
        self.btnExecute = QtGui.QPushButton(DlgSqlWindow)
        self.btnExecute.setObjectName(_fromUtf8("btnExecute"))
        self.hboxlayout.addWidget(self.btnExecute)
        self.lblResult = QtGui.QLabel(DlgSqlWindow)
        self.lblResult.setText(_fromUtf8(""))
        self.lblResult.setObjectName(_fromUtf8("lblResult"))
        self.hboxlayout.addWidget(self.lblResult)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)
        self.btnClear = QtGui.QPushButton(DlgSqlWindow)
        self.btnClear.setObjectName(_fromUtf8("btnClear"))
        self.hboxlayout.addWidget(self.btnClear)
        self.vboxlayout.addLayout(self.hboxlayout)
        self.label_2 = QtGui.QLabel(DlgSqlWindow)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.vboxlayout.addWidget(self.label_2)
        self.viewResult = QtGui.QTableView(DlgSqlWindow)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(3)
        sizePolicy.setHeightForWidth(self.viewResult.sizePolicy().hasHeightForWidth())
        self.viewResult.setSizePolicy(sizePolicy)
        self.viewResult.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.viewResult.setObjectName(_fromUtf8("viewResult"))
        self.vboxlayout.addWidget(self.viewResult)
        self.buttonBox = QtGui.QDialogButtonBox(DlgSqlWindow)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.vboxlayout.addWidget(self.buttonBox)

        self.retranslateUi(DlgSqlWindow)
        QtCore.QMetaObject.connectSlotsByName(DlgSqlWindow)
        DlgSqlWindow.setTabOrder(self.editSql, self.btnExecute)
        DlgSqlWindow.setTabOrder(self.btnExecute, self.btnClear)
        DlgSqlWindow.setTabOrder(self.btnClear, self.viewResult)
        DlgSqlWindow.setTabOrder(self.viewResult, self.buttonBox)

    def retranslateUi(self, DlgSqlWindow):
        DlgSqlWindow.setWindowTitle(QtGui.QApplication.translate("DlgSqlWindow", "SQL window", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("DlgSqlWindow", "SQL query:", None, QtGui.QApplication.UnicodeUTF8))
        self.btnExecute.setText(QtGui.QApplication.translate("DlgSqlWindow", "&Execute (F5)", None, QtGui.QApplication.UnicodeUTF8))
        self.btnExecute.setShortcut(QtGui.QApplication.translate("DlgSqlWindow", "F5", None, QtGui.QApplication.UnicodeUTF8))
        self.btnClear.setText(QtGui.QApplication.translate("DlgSqlWindow", "&Clear", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("DlgSqlWindow", "Result:", None, QtGui.QApplication.UnicodeUTF8))

