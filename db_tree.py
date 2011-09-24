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

from .db_model import DBModel

class DBTree(QTreeView):
	def __init__(self, parent=None):
		QTreeView.__init__(self, parent)
		self.setModel( DBModel(self) )
		self.setHeaderHidden(True)
		self.setDragEnabled(True)
		self.setAcceptDrops(True)
		self.setDropIndicatorShown(True)

		self.connect(self.selectionModel(), SIGNAL("currentChanged(const QModelIndex&, const QModelIndex&)"), self.itemChanged)
		self.connect(self, SIGNAL("expanded(const QModelIndex&)"), self.itemChanged)
		self.connect(self, SIGNAL("collapsed(const QModelIndex&)"), self.itemChanged)
		self.connect(self.model(), SIGNAL("dataChanged(const QModelIndex&, const QModelIndex&)"), self.itemChanged)
		self.connect(self.model(), SIGNAL("notPopulated"), self.collapse)

	def refreshItem(self, item=None):
		if item == None:
			item = self.currentItem()
			if item == None: return
		self.model().refreshItem(item)

	def showSystemTables(self, show):
		pass

	def currentItem(self):
		indexes = self.selectedIndexes()
		if len(indexes) <= 0:
			return
		return self.model().getItem(indexes[0])


	def currentDatabase(self):
		item = self.currentItem()
		if item == None: return
		try:
			return item.database()
		except TypeError:	# it's a DBPlugin class object, no database
			pass
		return None

	def currentSchema(self):
		item = self.currentItem()
		if item == None: return
		if hasattr(item, 'schema'): return item.schema()
		return None

	def currentTable(self):
		item = self.currentItem()
		if item == None: return
		from .db_plugins.plugin import Table
		if isinstance(item, Table):
			return item
		return None
			

	def itemChanged(self, indexFrom, indexTo=None):
		self.setCurrentIndex(indexFrom)
		self.emit( SIGNAL('currentChanged'), self.currentItem() )

