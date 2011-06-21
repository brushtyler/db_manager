# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/DlgDbError.ui'
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

class Ui_DlgDbError(object):
    def setupUi(self, DlgDbError):
        DlgDbError.setObjectName(_fromUtf8("DlgDbError"))
        DlgDbError.resize(400, 369)
        self.vboxlayout = QtGui.QVBoxLayout(DlgDbError)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.label = QtGui.QLabel(DlgDbError)
        self.label.setObjectName(_fromUtf8("label"))
        self.vboxlayout.addWidget(self.label)
        self.txtMessage = QtGui.QTextBrowser(DlgDbError)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.txtMessage.sizePolicy().hasHeightForWidth())
        self.txtMessage.setSizePolicy(sizePolicy)
        self.txtMessage.setObjectName(_fromUtf8("txtMessage"))
        self.vboxlayout.addWidget(self.txtMessage)
        self.label_2 = QtGui.QLabel(DlgDbError)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.vboxlayout.addWidget(self.label_2)
        self.txtQuery = QtGui.QTextBrowser(DlgDbError)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(3)
        sizePolicy.setHeightForWidth(self.txtQuery.sizePolicy().hasHeightForWidth())
        self.txtQuery.setSizePolicy(sizePolicy)
        self.txtQuery.setObjectName(_fromUtf8("txtQuery"))
        self.vboxlayout.addWidget(self.txtQuery)
        self.buttonBox = QtGui.QDialogButtonBox(DlgDbError)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.vboxlayout.addWidget(self.buttonBox)

        self.retranslateUi(DlgDbError)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), DlgDbError.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), DlgDbError.reject)
        QtCore.QMetaObject.connectSlotsByName(DlgDbError)

    def retranslateUi(self, DlgDbError):
        DlgDbError.setWindowTitle(QtGui.QApplication.translate("DlgDbError", "Database Error", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("DlgDbError", "An error occured when executing a query:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("DlgDbError", "Query:", None, QtGui.QApplication.UnicodeUTF8))

