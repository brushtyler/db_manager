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
from ui.dbmanager_ui import Ui_DBManager

class DBManager(QMainWindow, Ui_DBManager):

	def __init__(self, iface, parent=None):
		self.iface = iface
		QMainWindow.__init__(self, parent)
		self.setupUi(self)

		# restore the window state
		settings = QSettings()
		self.restoreGeometry( settings.value("/DB_Manager/geometry").toByteArray() )
		self.restoreState( settings.value("/DB_Manager/windowState").toByteArray() )

	def closeEvent(self, e):
		# save the window state
		settings = QSettings()
		settings.setValue( "/DB_Manager/windowState", QVariant(self.saveState()) )
		settings.setValue( "/DB_Manager/geometry", QVariant(self.saveGeometry()) )

		QMainWindow.closeEvent(self, e)


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

