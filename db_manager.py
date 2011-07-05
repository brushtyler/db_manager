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
		self.unregisterAllActions()

		# save the window state
		settings = QSettings()
		settings.setValue( "/DB_Manager/windowState", QVariant(self.saveState()) )
		settings.setValue( "/DB_Manager/geometry", QVariant(self.saveGeometry()) )

		QMainWindow.closeEvent(self, e)


	def refreshItem(self, item=None):
		self.tree.refreshItem(item)
		self.info.refresh()

	def removeItem(self, item=None):
		self.tree.refreshItem(item, True)


	def itemChanged(self, item):
		self.reloadButtons()
		self.refreshTabs( item )


	def reloadButtons(self):
		db = self.tree.currentDatabase()
		if not hasattr(self, '_lastDb'):
			self._lastDb = db
		elif db == self._lastDb:
			return

		# remove old actions
		if self._lastDb != None:
			self.unregisterAllActions()
			self.disconnect( self._lastDb, SIGNAL("contentChanged"), self.refreshItem )
			self.disconnect( self._lastDb, SIGNAL("contentRemoved"), self.removeItem )

		# add actions of the selected database
		self._lastDb = db
		if self._lastDb != None:
			self._lastDb.registerAllActions(self)
			self.connect( self._lastDb, SIGNAL("contentChanged"), self.refreshItem )
			self.connect( self._lastDb, SIGNAL("contentRemoved"), self.removeItem )


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
			QMessageBox.information(self, "Sorry", "No database selected or you are not connected.")
			return

		from dlg_sql_window import DlgSqlWindow
		dlg = DlgSqlWindow(self, db)
		dlg.exec_()
		self.refreshItem( db.connection() )

	def deleteSchema(self):
		item = self.tree.currentSchema()
		if item == None:
			QMessageBox.information(self, "Sorry", "Select a SCHEMA for deletion.")
			return
		res = QMessageBox.question(self, "hey!", u"Really delete schema %s ?" % item.name, QMessageBox.Yes | QMessageBox.No)
		if res != QMessageBox.Yes:
			return
		item.delete()

	def deleteTable(self):
		item = self.tree.currentTable()
		if item == None:
			QMessageBox.information(self, "Sorry", "Select a TABLE or VIEW for deletion.")
			return
		res = QMessageBox.question(self, "hey!", u"Really delete table/view %s ?" % item.name, QMessageBox.Yes | QMessageBox.No)
		if res != QMessageBox.Yes:
			return
		item.delete()



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
		return callback( selected_item, action, self ) 

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

