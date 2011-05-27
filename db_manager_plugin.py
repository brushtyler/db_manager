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

class DBManagerPlugin:
	def __init__(self, iface):
		self.iface = iface

	def initGui(self):
		self.action = QAction( QIcon(), self.tr( u"DB Manager" ), self.iface.mainWindow() )
		QObject.connect( self.action, SIGNAL( "triggered()" ), self.run )
		self.iface.addToPluginDatabaseMenu( self.tr( u"DB Manager" ), self.action )

	def unload(self):
		self.iface.removePluginDatabaseMenu( self.action )

	def run(self):
		from db_manager import DBManager
		self.dlg = DBManager(self.iface, self.iface.mainWindow())
		self.dlg.show()
		self.dlg.exec_()

