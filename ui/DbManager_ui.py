# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/DbManager.ui'
#
# Created: Tue Jun 21 04:30:06 2011
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_DBManager(object):
    def setupUi(self, DBManager):
        DBManager.setObjectName(_fromUtf8("DBManager"))
        DBManager.resize(800, 535)
        self.centralwidget = QtGui.QWidget(DBManager)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout_3 = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.splitter = QtGui.QSplitter(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.splitter.sizePolicy().hasHeightForWidth())
        self.splitter.setSizePolicy(sizePolicy)
        self.splitter.setMinimumSize(QtCore.QSize(696, 0))
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.treeView = DBTree(self.splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.treeView.sizePolicy().hasHeightForWidth())
        self.treeView.setSizePolicy(sizePolicy)
        self.treeView.setObjectName(_fromUtf8("treeView"))
        self.tabWidget = QtGui.QTabWidget(self.splitter)
        self.tabWidget.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(3)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.infoTab = InfoViewer()
        self.infoTab.setEnabled(True)
        self.infoTab.setObjectName(_fromUtf8("infoTab"))
        self.infoTabLayout = QtGui.QGridLayout(self.infoTab)
        self.infoTabLayout.setObjectName(_fromUtf8("infoTabLayout"))
        self.tabWidget.addTab(self.infoTab, _fromUtf8(""))
        self.tableTab = QtGui.QWidget()
        self.tableTab.setEnabled(True)
        self.tableTab.setObjectName(_fromUtf8("tableTab"))
        self.tableTabLayout = QtGui.QGridLayout(self.tableTab)
        self.tableTabLayout.setObjectName(_fromUtf8("tableTabLayout"))
        self.tabWidget.addTab(self.tableTab, _fromUtf8(""))
        self.previewTab = QtGui.QWidget()
        self.previewTab.setEnabled(True)
        self.previewTab.setObjectName(_fromUtf8("previewTab"))
        self.previewTabLayout = QtGui.QGridLayout(self.previewTab)
        self.previewTabLayout.setObjectName(_fromUtf8("previewTabLayout"))
        self.tabWidget.addTab(self.previewTab, _fromUtf8(""))
        self.gridLayout_3.addWidget(self.splitter, 0, 0, 1, 1)
        DBManager.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(DBManager)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 25))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        DBManager.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(DBManager)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        DBManager.setStatusBar(self.statusbar)
        self.toolBar = QtGui.QToolBar(DBManager)
        self.toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.toolBar.setObjectName(_fromUtf8("toolBar"))
        DBManager.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.actionRefresh = QtGui.QAction(DBManager)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/db_manager/icons/toolbar/action_refresh.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionRefresh.setIcon(icon)
        self.actionRefresh.setObjectName(_fromUtf8("actionRefresh"))
        self.actionExit = QtGui.QAction(DBManager)
        self.actionExit.setObjectName(_fromUtf8("actionExit"))
        self.actionRunQuery = QtGui.QAction(DBManager)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8(":/db_manager/icons/toolbar/action_sql_window.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionRunQuery.setIcon(icon1)
        self.actionRunQuery.setObjectName(_fromUtf8("actionRunQuery"))
        self.menuFile.addAction(self.actionRefresh)
        self.menuFile.addAction(self.actionRunQuery)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menubar.addAction(self.menuFile.menuAction())
        self.toolBar.addAction(self.actionRefresh)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionRunQuery)

        self.retranslateUi(DBManager)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(DBManager)

    def retranslateUi(self, DBManager):
        DBManager.setWindowTitle(QtGui.QApplication.translate("DBManager", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.infoTab), QtGui.QApplication.translate("DBManager", "Info", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tableTab), QtGui.QApplication.translate("DBManager", "Table", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.previewTab), QtGui.QApplication.translate("DBManager", "Preview", None, QtGui.QApplication.UnicodeUTF8))
        self.menuFile.setTitle(QtGui.QApplication.translate("DBManager", "File", None, QtGui.QApplication.UnicodeUTF8))
        self.toolBar.setWindowTitle(QtGui.QApplication.translate("DBManager", "toolBar", None, QtGui.QApplication.UnicodeUTF8))
        self.actionRefresh.setText(QtGui.QApplication.translate("DBManager", "&Refresh", None, QtGui.QApplication.UnicodeUTF8))
        self.actionRefresh.setToolTip(QtGui.QApplication.translate("DBManager", "Refresh", None, QtGui.QApplication.UnicodeUTF8))
        self.actionRefresh.setShortcut(QtGui.QApplication.translate("DBManager", "F5", None, QtGui.QApplication.UnicodeUTF8))
        self.actionExit.setText(QtGui.QApplication.translate("DBManager", "&Exit", None, QtGui.QApplication.UnicodeUTF8))
        self.actionExit.setShortcut(QtGui.QApplication.translate("DBManager", "Ctrl+Q", None, QtGui.QApplication.UnicodeUTF8))
        self.actionRunQuery.setText(QtGui.QApplication.translate("DBManager", "&SQL window...", None, QtGui.QApplication.UnicodeUTF8))
        self.actionRunQuery.setToolTip(QtGui.QApplication.translate("DBManager", "Run queries on the selected database", None, QtGui.QApplication.UnicodeUTF8))
        self.actionRunQuery.setShortcut(QtGui.QApplication.translate("DBManager", "F2", None, QtGui.QApplication.UnicodeUTF8))

from ..info_viewer import InfoViewer
from ..db_tree import DBTree
from .. import resources_rc
