# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name                 : DB Manager
Description          : Database manager plugin for QuantumGIS
Date                 : May 23, 2011
copyright            : (C) 2011 by Giuseppe Sucameli
email                : brush.tyler@gmail.com

 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .info_viewer import InfoViewer
from .layer_preview import LayerPreview
from .db_tree import DBTree


class DBManager(QMainWindow):

	def __init__(self, iface, parent=None):
		QMainWindow.__init__(self, parent)
		self.setAttribute(Qt.WA_DeleteOnClose)
		self.setupUi()
		self.iface = iface

		# restore the window state
		settings = QSettings()
		self.restoreGeometry( settings.value("/DB_Manager/geometry").toByteArray() )
		self.restoreState( settings.value("/DB_Manager/windowState").toByteArray() )

		self.connect(self.tree, SIGNAL("currentChanged"), self.itemChanged)
		self.itemChanged(None)

	def closeEvent(self, e):
		# save the window state
		settings = QSettings()
		settings.setValue( "/DB_Manager/windowState", QVariant(self.saveState()) )
		settings.setValue( "/DB_Manager/geometry", QVariant(self.saveGeometry()) )

		QMainWindow.closeEvent(self, e)


	def itemChanged(self, item):
		self.refreshTabs( item )

	def refreshTabs(self, item):
		# enable/disable tabs
		self.tabs.setTabEnabled( self.tabs.indexOf(self.info), item != None )
		self.tabs.setTabEnabled( self.tabs.indexOf(self.table), False )
		self.tabs.setTabEnabled( self.tabs.indexOf(self.preview), False )

		if not self.tabs.isTabEnabled( self.tabs.currentIndex() ):
			for i in range(self.tabs.count()):
				if self.tabs.isTabEnabled( i ):
					self.tabs.setCurrentWidget(i)
					break

		current_tab = self.tabs.currentWidget()
		if current_tab == self.info:
			self.info.showInfo( item )
		elif current_tab == self.table:
			pass
		elif current_tab == self.preview:
			self.preview.load( item )


	def showSqlWindow(self):
		db = self.tree.currentDatabase()
		if db == None:
			QMessageBox.information(self, u"Sorry", u"No database selected or you are not connected.")
			return

		from dlg_sql_window import DlgSqlWindow
		dlg = DlgSqlWindow(self, db)
		dlg.exec_()
		self.emit( SIGNAL('reloadDatabase'), db)

	def refreshDatabase(self):
		pass


	def registerAction(self, action, menu, callback):
		""" register an action to the manager's main menu """
		invoke_callback = lambda x: self.__invokeCallback( callback, checked )
		for a in self.menuBar().actions():
			if not a.menu() or a.menu().text() != menu:
				continue
			a.menu().addAction( action )
			QObject.connect( action, SIGNAL("triggered(bool)"), invoke_callback )
			return True
		return False

	def __invokeCallback(self, callback, checked):
		action = self.sender
		return callback( self.dbPlugin, checked, self.__currentDBTreeItem() ) 

	def unregisterAction(self, action, menu):
		for a in self.menuBar().actions():
			if not a.menu() or a.menu().text() != menu:
				continue
			a.menu().removeAction( action )
			return True
		return False


	def setupUi(self):
		self.setWindowTitle("DB Manager")
		self.setWindowIcon(QIcon(":/db_manager/icon"))
		self.resize(QSize(700,500).expandedTo(self.minimumSizeHint()))

		# create central tab widget
		self.tabs = QTabWidget()
		self.info = InfoViewer(self)
		self.tabs.addTab(self.info, "Info")
		self.table = QWidget(self)
		self.tabs.addTab(self.table, "Table")
		self.preview = LayerPreview(self)
		self.tabs.addTab(self.preview, "Preview")
		self.setCentralWidget(self.tabs)

		# create database tree
		self.dock = QDockWidget("Databases", self)
		self.dock.setObjectName("DB_Manager_DBView")
		self.dock.setFeatures(QDockWidget.DockWidgetMovable)
		self.tree = DBTree(self)
		self.dock.setWidget(self.tree)
		self.addDockWidget(Qt.LeftDockWidgetArea, self.dock)

		# create status bar
		self.statusBar = QStatusBar(self)
		self.setStatusBar(self.statusBar)		

		# create menus
		self.menuBar = QMenuBar(self)
		self.menuDb = QMenu("&Database", self)
		self.menuBar.addMenu(self.menuDb)
		self.menuHelp = QMenu("&Help", self)
		self.menuBar.addMenu(self.menuHelp)
		self.setMenuBar(self.menuBar)

		# create toolbar
		self.toolBar = QToolBar(self)
		self.toolBar.setObjectName("DB_Manager_ToolBar")
		self.toolBar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
		self.addToolBar(self.toolBar)

		# create menus' actions
		self.actionRefresh = self.menuDb.addAction( QIcon(":/db_manager/refresh"), "&Refresh", self.refreshDatabase, QKeySequence("F5") )
		self.actionSqlWindow = self.menuDb.addAction( QIcon(":/db_manager/sql_window"), "&SQL window", self.showSqlWindow, QKeySequence("F2") )
		self.actionClose = self.menuDb.addAction( QIcon(), u"Exit", self.close, QKeySequence("CTRL+Q") )

		# add actions to the toolbar
		self.toolBar.addAction( self.actionRefresh )
		self.toolBar.addAction( self.actionSqlWindow )

