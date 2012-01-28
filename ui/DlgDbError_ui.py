# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/DlgDbError.ui'
#
# Created: Sat Jan 28 01:55:09 2012
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
        DlgDbError.resize(400, 314)
        self.verticalLayout_2 = QtGui.QVBoxLayout(DlgDbError)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.stackedWidget = QtGui.QStackedWidget(DlgDbError)
        self.stackedWidget.setObjectName(_fromUtf8("stackedWidget"))
        self.page_2 = QtGui.QWidget()
        self.page_2.setObjectName(_fromUtf8("page_2"))
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.page_2)
        self.verticalLayout_3.setMargin(0)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.label_3 = QtGui.QLabel(self.page_2)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.verticalLayout_3.addWidget(self.label_3)
        self.txtErrorMsg = QtGui.QTextBrowser(self.page_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.txtErrorMsg.sizePolicy().hasHeightForWidth())
        self.txtErrorMsg.setSizePolicy(sizePolicy)
        self.txtErrorMsg.setObjectName(_fromUtf8("txtErrorMsg"))
        self.verticalLayout_3.addWidget(self.txtErrorMsg)
        self.stackedWidget.addWidget(self.page_2)
        self.page = QtGui.QWidget()
        self.page.setObjectName(_fromUtf8("page"))
        self.verticalLayout = QtGui.QVBoxLayout(self.page)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(self.page)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.txtQueryErrorMgs = QtGui.QTextBrowser(self.page)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.txtQueryErrorMgs.sizePolicy().hasHeightForWidth())
        self.txtQueryErrorMgs.setSizePolicy(sizePolicy)
        self.txtQueryErrorMgs.setObjectName(_fromUtf8("txtQueryErrorMgs"))
        self.verticalLayout.addWidget(self.txtQueryErrorMgs)
        self.label_2 = QtGui.QLabel(self.page)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout.addWidget(self.label_2)
        self.txtQuery = QtGui.QTextBrowser(self.page)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(3)
        sizePolicy.setHeightForWidth(self.txtQuery.sizePolicy().hasHeightForWidth())
        self.txtQuery.setSizePolicy(sizePolicy)
        self.txtQuery.setObjectName(_fromUtf8("txtQuery"))
        self.verticalLayout.addWidget(self.txtQuery)
        self.stackedWidget.addWidget(self.page)
        self.verticalLayout_2.addWidget(self.stackedWidget)
        self.buttonBox = QtGui.QDialogButtonBox(DlgDbError)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout_2.addWidget(self.buttonBox)

        self.retranslateUi(DlgDbError)
        self.stackedWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), DlgDbError.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), DlgDbError.reject)
        QtCore.QMetaObject.connectSlotsByName(DlgDbError)

    def retranslateUi(self, DlgDbError):
        DlgDbError.setWindowTitle(QtGui.QApplication.translate("DlgDbError", "Database Error", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("DlgDbError", "An error occured:", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("DlgDbError", "An error occured when executing a query:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("DlgDbError", "Query:", None, QtGui.QApplication.UnicodeUTF8))

