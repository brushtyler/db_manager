# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name                 : DB Manager
Description          : Database manager plugin for QuantumGIS
Date                 : May 23, 2011
copyright            : (C) 2011 by Giuseppe Sucameli
email                : brush.tyler@gmail.com

The content of this file is based on PostGIS Manager by Martin Dobias
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

from . import db_plugins
try:
	from . import resources_rc
except ImportError:
	pass

class TreeItem(QObject):
	def __init__(self, data, parent=None):
		QObject.__init__(self, parent)
		self.parentItem = parent
		self.itemData = data
		self.childItems = []
		if parent:
			parent.appendChild(self)

	def getItemData(self):
		return self.itemData
			
	def appendChild(self, child):
		self.childItems.append(child)
	
	def child(self, row):
		return self.childItems[row]
	
	def childCount(self):
		return len(self.childItems)

	def columnCount(self):
		return 1
	
	def row(self):
		if self.parentItem:
			for row, item in enumerate(self.parentItem.childItems):
				if item is self:
					return row
		return 0

	def data(self, column):
		return "" if column == 0 else None
	
	def parent(self):
		return self.parentItem
	
	def icon(self):
		return None


class PluginItem(TreeItem):
	def __init__(self, dbplugin, parent=None):
		TreeItem.__init__(self, dbplugin, parent)

		# create items for connections
		for c in self.getItemData().connections():
			ConnectionItem(c, self)

	def data(self, column):
		if column == 0:
			return self.getItemData().typeNameString()
		return None

	def icon(self):
		return self.getItemData().icon()


class ConnectionItem(TreeItem):
	def __init__(self, db, parent=None):
		TreeItem.__init__(self, db, parent)
		self.populated = False

	def data(self, column):
		if column == 0:
			return self.getItemData().connectionName()
		return None
		
	def populate(self):
		if self.populated:
			return True

		db = self.getItemData()
		try:
			if not db.connect():
				return False

		except (db_plugins.InvalidDataException, db_plugins.DbError), e:
			QMessageBox.warning( None, u"Unable to connect", unicode(e) )
			return False

		schemas = db.connector.schemas()
		if schemas != None:
			for s in schemas:
				SchemaItem(s, self)
		else:
			tables = db.connector.tables()
			for t in tables:
				TableItem(t, self)

		self.populated = True
		return True


class SchemaItem(TreeItem):
	def __init__(self, schema, parent):
		TreeItem.__init__(self, schema, parent)
		self.populated = False

		# load (shared) icon with first instance of schema item
		if not hasattr(SchemaItem, 'schemaIcon'):
			SchemaItem.schemaIcon = QIcon(":/icons/namespace.png")

	def data(self, column):
		if column == 0:
			return self.getItemData().name
		return None
	
	def icon(self):
		return self.schemaIcon
	
	def populate(self):
		if self.populated:
			return True

		schema = self.getItemData()
		db = self.parent().getItemData()
		for t in db.connector.tables( schema.name ):
			TableItem(t, self)
		self.populated = True
		return True


class TableItem(TreeItem):
	def __init__(self, table, parent):
		TreeItem.__init__(self, table, parent)
		
		# load (shared) icon with first instance of table item
		if not hasattr(TableItem, 'tableIcon'):
			TableItem.tableIcon = QIcon(":/icons/table.png")
			TableItem.viewIcon = QIcon(":/icons/view.png")
			TableItem.layerPointIcon = QIcon(":/icons/layer_point.png")
			TableItem.layerLineIcon = QIcon(":/icons/layer_line.png")
			TableItem.layerPolygonIcon = QIcon(":/icons/layer_polygon.png")
			TableItem.layerUnknownIcon = QIcon(":/icons/layer_unknown.png")
			
	def data(self, column):
		if column == 0:
			return self.getItemData().name
		elif column == 1:
			return self.getItemData().geomType
		return None

	def childCount(self):
		return 0
		
	def icon(self):
		geom_type = self.getItemData().geomType
		if geom_type is not None:
			if geom_type.find('POINT') != -1:
				return self.layerPointIcon
			elif geom_type.find('LINESTRING') != -1:
				return self.layerLineIcon
			elif geom_type.find('POLYGON') != -1:
				return self.layerPolygonIcon
			return self.layerUnknownIcon

		if self.getItemData().isView:
			return self.viewIcon
		return self.tableIcon


class DBModel(QAbstractItemModel):
	
	def __init__(self, parent=None):
		QAbstractItemModel.__init__(self, parent)
		self.header = ['Table']

		self.rootItem = TreeItem(None, None)
		for dbtype in db_plugins.supportedDBTypes():
			dbpluginclass = db_plugins.create( dbtype )
			PluginItem( dbpluginclass, self.rootItem )


	def getItem(self, index):
		if not index.isValid():
			return None
		return index.internalPointer().getItemData() 


	def columnCount(self, parent):
		return 1
		
	def data(self, index, role):
		if not index.isValid():
			return QVariant()
		
		if role == Qt.DecorationRole and index.column() == 0:
			icon = index.internalPointer().icon()
			if icon: return QVariant(icon)
			
		if role != Qt.DisplayRole and role != Qt.EditRole:
			return QVariant()
		
		retval = index.internalPointer().data(index.column())
		return QVariant(retval) if retval else QVariant()
	
	def flags(self, index):
		if not index.isValid():
			return 0
		
		flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable 
		if index.column() == 0:
			item = index.internalPointer()
			if isinstance(item, SchemaItem) or isinstance(item, TableItem):
				flags |= Qt.ItemIsEditable
		return flags
	
	def headerData(self, section, orientation, role):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole and section < len(self.header):
			return QVariant(self.header[section])
		return QVariant()

	def index(self, row, column, parent):
		if not self.hasIndex(row, column, parent):
			return QModelIndex()
		
		parentItem = parent.internalPointer() if parent.isValid() else self.rootItem
		childItem = parentItem.child(row)
		if childItem:
			return self.createIndex(row, column, childItem)
		return QModelIndex()

	def parent(self, index):
		if not index.isValid():
			return QModelIndex()
		
		childItem = index.internalPointer()
		parentItem = childItem.parent()

		if parentItem == self.rootItem:
			return QModelIndex()
		
		return self.createIndex(parentItem.row(), 0, parentItem)


	def rowCount(self, parent):
		parentItem = parent.internalPointer() if parent.isValid() else self.rootItem
		return parentItem.childCount()

	def hasChildren(self, parent):
		parentItem = parent.internalPointer() if parent.isValid() else self.rootItem
		return parentItem.childCount() > 0 or (hasattr(parentItem, 'populated') and parentItem.populated == False)

	def canFetchMore(self, parent):
		parentItem = parent.internalPointer() if parent.isValid() else self.rootItem
		return hasattr(parentItem, 'populated') and parentItem.populated == False

	def fetchMore(self, parent):
		parentItem = parent.internalPointer() if parent.isValid() else self.rootItem
		if hasattr(parentItem, 'populate'):
			parentItem.populate()


	def setData(self, index, value, role):
		if role != Qt.EditRole or index.column() != 0:
			return False
			
		item = index.internalPointer()
		new_name = unicode(value.toString())
		if new_name == item.name:
			return False
		
		if isinstance(item, SchemaItem) or isinstance(item, TableItem):
			# rename schema or table or view
			try:
				item.getItemData().rename(new_name)
				self.emit(SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'), index, index)
				return True
			except db_plugins.DbError, e:
				DlgDbError.showError(e, None)
				return False

		return False

