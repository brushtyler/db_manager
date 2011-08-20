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
from .table_viewer import TableViewer
from .layer_preview import LayerPreview

from .db_tree import DBTree

from .db_plugins.plugin import DbError, Table
from .dlg_db_error import DlgDbError


class DBManager(QMainWindow):

	def __init__(self, iface, parent=None):
		QMainWindow.__init__(self, parent)
		self.setAttribute(Qt.WA_DeleteOnClose)
		self.setupUi()
		self.iface = iface

		# restore the window state
		settings = QSettings()
		self.restoreGeometry( settings.value("/DB_Manager/mainWindow/geometry").toByteArray() )
		self.restoreState( settings.value("/DB_Manager/mainWindow/windowState").toByteArray() )

		self.connect(self.tabs, SIGNAL("currentChanged(int)"), self.tabChanged)
		self.connect(self.tree, SIGNAL("currentChanged"), self.itemChanged)
		self.itemChanged(None)

	def closeEvent(self, e):
		self.unregisterAllActions()

		# save the window state
		settings = QSettings()
		settings.setValue( "/DB_Manager/mainWindow/windowState", QVariant(self.saveState()) )
		settings.setValue( "/DB_Manager/mainWindow/geometry", QVariant(self.saveGeometry()) )

		QMainWindow.closeEvent(self, e)


	def refreshItem(self, item=None):
		if item == None:
			item = self.tree.currentItem()
		self.tree.refreshItem(item)	# refresh item children in the db tree


	def itemChanged(self, item):
		self.reloadButtons()
		self.refreshTabs()

	def reloadButtons(self):
		db = self.tree.currentDatabase()
		if not hasattr(self, '_lastDb'):
			self._lastDb = db

		elif db == self._lastDb:
			return

		# remove old actions
		if self._lastDb != None:
			self.unregisterAllActions()

		# add actions of the selected database
		self._lastDb = db
		if self._lastDb != None:
			self._lastDb.registerAllActions(self)


	def tabChanged(self, index):
		self.refreshTabs()

	def refreshTabs(self):
		index = self.tabs.currentIndex()
		item  = self.tree.currentItem()
		table  = self.tree.currentTable()

		# enable/disable tabs
		self.tabs.setTabEnabled( self.tabs.indexOf(self.table), table != None )
		self.tabs.setTabEnabled( self.tabs.indexOf(self.preview), table != None and table.type == Table.VectorType and table.geomColumn != None )

		# show the info tab if the current tab is disabled
		if not self.tabs.isTabEnabled( index ):
			self.tabs.setCurrentWidget( self.info )

		current_tab = self.tabs.currentWidget()
		if current_tab == self.info:
			self.info.showInfo( item, True ) # force refresh
		elif current_tab == self.table:
			self.table.loadData( item )
		elif current_tab == self.preview:
			self.preview.loadPreview( item )

	def showSqlWindow(self):
		db = self.tree.currentDatabase()
		if db == None:
			QMessageBox.information(self, "Sorry", "No database selected or you are not connected to it.")
			return

		from dlg_sql_window import DlgSqlWindow
		dlg = DlgSqlWindow(self, db)
		dlg.exec_()
		self.refreshItem( db.connection() )


	def registerAction(self, action, menu, callback):
		""" register an action to the manager's main menu """
		if not hasattr(self, '_registeredDbActions'):
			self._registeredDbActions = []

		invoke_callback = lambda x: self.__invokeCallback( callback )
		for a in self.menuBar.actions():
			if not a.menu() or a.menu().title() != menu:
				continue
			a.menu().addAction( action )
			self._registeredDbActions.append( (action, menu) )
			a.setVisible(True)	# show the menu
			QObject.connect( action, SIGNAL("triggered(bool)"), invoke_callback )
			return True
		return False

	def __invokeCallback(self, callback):
		action = self.sender
		selected_item = self.tree.currentItem()
		try:
			callback( selected_item, action, self ) 
		except DbError, e:
			DlgDbError.showError(e, self)

	def unregisterAction(self, action, menu):
		if not hasattr(self, '_registeredDbActions'):
			return

		for a in self.menuBar.actions():
			if not a.menu() or a.menu().title() != menu:
				continue
			a.menu().removeAction( action )
			if self._registeredDbActions.count( (action, menu) ) > 0:
				self._registeredDbActions.remove( (action, menu) )
			action.deleteLater()
			if a.menu().isEmpty():	# hide the menu
				a.setVisible(False)
			return True
		return False

	def unregisterAllActions(self):
		if not hasattr(self, '_registeredDbActions'):
			return

		for action, menu in list(self._registeredDbActions):
			self.unregisterAction( action, menu )
		self._registeredDbActions = []


	def setupUi(self):
		self.setWindowTitle("DB Manager")
		self.setWindowIcon(QIcon(":/db_manager/icon"))
		self.resize(QSize(700,500).expandedTo(self.minimumSizeHint()))

		# create central tab widget
		self.tabs = QTabWidget()
		self.info = InfoViewer(self)
		self.tabs.addTab(self.info, "Info")
		self.table = TableViewer(self)
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
		self.menuSchema = QMenu("&Schema", self)
		self.menuBar.addMenu(self.menuSchema).setVisible(False)
		self.menuTable = QMenu("&Table", self)
		self.menuBar.addMenu(self.menuTable).setVisible(False)
		self.menuHelp = QMenu("&Help", self)
		self.menuBar.addMenu(self.menuHelp)

		self.setMenuBar(self.menuBar)

		# create toolbar
		self.toolBar = QToolBar(self)
		self.toolBar.setObjectName("DB_Manager_ToolBar")
		self.toolBar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
		self.addToolBar(self.toolBar)

		# create menus' actions
		# menu DATABASE
		self.actionRefresh = self.menuDb.addAction( QIcon(":/db_manager/actions/refresh"), "&Refresh", self.refreshItem, QKeySequence("F5") )
		self.actionSqlWindow = self.menuDb.addAction( QIcon(":/db_manager/actions/sql_window"), "&SQL window", self.showSqlWindow, QKeySequence("F2") )
		self.actionClose = self.menuDb.addAction( QIcon(), "&Exit", self.close, QKeySequence("CTRL+Q") )

		# menu HELP
		#self.actionAbout = self.menuHelp.addAction("&About", self.about)

		# add actions to the toolbar
		self.toolBar.addAction( self.actionRefresh )
		self.toolBar.addAction( self.actionSqlWindow )

