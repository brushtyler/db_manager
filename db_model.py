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

from .db_plugins import supportedDbTypes, createDbPlugin
from .db_plugins.plugin import InvalidDataException, ConnectionError

try:
	from . import resources_rc
except ImportError:
	pass

class TreeItem(QObject):
	def __init__(self, data, parent=None):
		QObject.__init__(self, parent)
		self.populated = False
		self.itemData = data
		self.childItems = []
		if parent: 
			parent.appendChild(self)

	def populate(self):
		self.populated = True
		return True

	def getItemData(self):
		return self.itemData
			
	def appendChild(self, child):
		self.childItems.append(child)
	
	def child(self, row):
		return self.childItems[row]

	def removeChild(self, row):
		if row >= 0 and row < len(self.childItems):
			self.childItems[row].itemData.deleteLater()
			del self.childItems[row]
	
	def childCount(self):
		return len(self.childItems)

	def columnCount(self):
		return 1
	
	def row(self):
		if self.parent():
			for row, item in enumerate(self.parent().childItems):
				if item is self:
					return row
		return 0

	def data(self, column):
		return "" if column == 0 else None
	
	def icon(self):
		return None


class PluginItem(TreeItem):
	def __init__(self, dbplugin, parent=None):
		TreeItem.__init__(self, dbplugin, parent)
		self.populate()

	def populate(self):
		if self.populated:
			return True

		# create items for connections
		for c in self.getItemData().connections():
			ConnectionItem(c, self)

		self.populated = True
		QApplication.restoreOverrideCursor()
		return True


	def data(self, column):
		if column == 0:
			return self.getItemData().typeNameString()
		return None

	def icon(self):
		return self.getItemData().icon()


class ConnectionItem(TreeItem):
	def __init__(self, connection, parent=None):
		TreeItem.__init__(self, connection, parent)

	def data(self, column):
		if column == 0:
			return self.getItemData().connectionName()
		return None

	def populate(self):
		if self.populated:
			return True

		connection = self.getItemData()
		if connection.database() == None:
			# connect to database
			try:
				if not connection.connect():
					return False

			except (InvalidDataException, ConnectionError), e:
				QMessageBox.warning( None, u"Unable to connect", unicode(e) )
				return False

		QApplication.setOverrideCursor(Qt.WaitCursor)
		schemas = connection.database().schemas()
		if schemas != None:
			for s in schemas:
				SchemaItem(s, self)
		else:
			tables = connection.database().tables()
			for t in tables:
				TableItem(t, self)

		self.populated = True
		QApplication.restoreOverrideCursor()
		return True


class SchemaItem(TreeItem):
	def __init__(self, schema, parent):
		TreeItem.__init__(self, schema, parent)

		# load (shared) icon with first instance of schema item
		if not hasattr(SchemaItem, 'schemaIcon'):
			SchemaItem.schemaIcon = QIcon(":/db_manager/icons/namespace.png")

	def data(self, column):
		if column == 0:
			return self.getItemData().name
		return None
	
	def icon(self):
		return self.schemaIcon
	
	def populate(self):
		if self.populated:
			return True

		QApplication.setOverrideCursor(Qt.WaitCursor)
		for t in self.getItemData().tables():
			TableItem(t, self)

		self.populated = True
		QApplication.restoreOverrideCursor()
		return True


class TableItem(TreeItem):
	def __init__(self, table, parent):
		TreeItem.__init__(self, table, parent)
		self.populate()
		
		# load (shared) icon with first instance of table item
		if not hasattr(TableItem, 'tableIcon'):
			TableItem.tableIcon = QIcon(":/db_manager/icons/table.png")
			TableItem.viewIcon = QIcon(":/db_manager/icons/view.png")
			TableItem.layerPointIcon = QIcon(":/db_manager/icons/layer_point.png")
			TableItem.layerLineIcon = QIcon(":/db_manager/icons/layer_line.png")
			TableItem.layerPolygonIcon = QIcon(":/db_manager/icons/layer_polygon.png")
			TableItem.layerUnknownIcon = QIcon(":/db_manager/icons/layer_unknown.png")
			
	def data(self, column):
		if column == 0:
			return self.getItemData().name
		elif column == 1:
			return self.getItemData().geomType
		return None
		
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
		self.header = ['Databases']

		self.rootItem = TreeItem(None, None)
		for dbtype in supportedDbTypes():
			dbpluginclass = createDbPlugin( dbtype )
			PluginItem( dbpluginclass, self.rootItem )


	def refreshItem(self, item, removed=False):
		# find the index for the item
		index = self._rItem2Index( self._createPathForItem(item) )
		if index.isValid():
			if removed:
				# remove child
				self.removeRows(index.row(), 1, index.parent())
				self._onDataChanged(index.parent())
			else:
				self.refreshIndex(index)

	def _createPathForItem(self, item):
		path = []
		if item == None:
			return path
		try:
			if item.database() != None:
				path.append( createDbPlugin(item.database().connection().typeName()) )
		except TypeError:
			path.append( item )	# it's a DBPlugin class object, no database
		else:
			from .db_plugins.plugin import DBPlugin, Schema, Table
			if isinstance(item, Table):
				if item.schema() != None:
					path.extend( [item.database().connection(), item.schema(), item] )
				else:
					path.extend( [item.database().connection(), item] )
			elif isinstance(item, Schema):
				path.extend( [item.database().connection(), item] )
			else:
				path.append( item )
		return path

	def _rItem2Index(self, item, parent=None):
		if parent == None:
			parent = QModelIndex()
		if item == None or len(item) == 0:
			return parent
		for i in range( self.rowCount(parent) ):
			index = self.index(i, 0, parent)
			if self.getItem( index ) == item[0]:
				return self._rItem2Index( item[1:], index )
		return QModelIndex()


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
		if not parentItem.populated and parentItem.populate():
			self._onDataChanged( parent )
		return parentItem.childCount()

	def hasChildren(self, parent):
		parentItem = parent.internalPointer() if parent.isValid() else self.rootItem
		return parentItem.childCount() > 0 or not parentItem.populated


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
				self._onDataChanged(index)
				return True
			except DbError, e:
				DlgDbError.showError(e, None)
				return False

		return False

	def removeRows(self, row, count, parent):
		self.beginRemoveRows(parent, row, count+row-1)
		item = parent.internalPointer()
		for i in range(row, count+row):
			item.removeChild(row)
		self.endRemoveRows()

	def refreshIndex(self, index):
		self.removeRows(0, self.rowCount(index), index)
		index.internalPointer().populated = False
		if index.internalPointer().populate():
			self._onDataChanged(index)		

	def _onDataChanged(self, indexFrom, indexTo=None):
		if indexTo == None: indexTo = indexFrom
		self.emit( SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'), indexFrom, indexTo)

