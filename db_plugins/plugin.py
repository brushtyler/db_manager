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

from ..db_plugins import createDbPlugin

class InvalidDataException(Exception):
	def __init__(self, msg):
		self.msg = unicode( msg )
		Exception(self, self.msg)

	def __str__(self):
		return self.msg.encode('utf-8')

class ConnectionError(Exception):
	def __init__(self, msg):
		self.msg = unicode( msg )
		Exception(self, self.msg)

	def __str__(self):
		return self.msg.encode('utf-8')

class DbError(Exception):
	def __init__(self, errormsg, query=None):
		self.msg = unicode( errormsg )
		self.query = unicode( query ) if query else None
		Exception(self, self.msg)

	def __str__(self):
		msg = self.msg
		if self.query:
			msg += u"\nQuery:\n%s" % self.query
		return msg.encode('utf-8')


class DBPlugin(QObject):
	def __init__(self, conn_name, parent=None):
		QObject.__init__(self, parent)
		self.connName = conn_name
		self.db = None

	def __del__(self):
		print "DBPlugin.__del__", self.connName

	def connectionName(self):
		return self.connName

	def database(self):
		return self.db

	def connect(self):
		return False

	@classmethod
	def icon(self):
		return None

	@classmethod
	def typeName(self):
		# return the db typename (e.g. 'postgis')
		pass

	@classmethod
	def typeNameString(self):
		# return the db typename string (e.g. 'PostGIS')
		pass

	@classmethod
	def connectionSettingsKey(self):
		# return the key used to store the connections in settings
		pass

	@classmethod
	def connections(self):
		# get the list of connections
		conn_list = []
		settings = QSettings()
		settings.beginGroup( self.connectionSettingsKey() )
		for name in settings.childGroups():
			conn_list.append( createDbPlugin(self.typeName(), name) )
		settings.endGroup()
		return conn_list


	def databasesFactory(self, connection, uri):
		return None


class Item(QObject):
	def __init__(self, parent=None):
		QObject.__init__(self, parent)

	def database(self):
		return None

	def generalInfo(self):
		return []

	def privilegesDetails(self):
		return None

	def spatialInfo(self):
		return None

	def runAction(self):
		pass


class Database(Item):
	def __init__(self, dbplugin, uri):
		QObject.__init__(self, dbplugin)
		self.connector = self.connectorsFactory( uri )

	def connectorsFactory(self, uri):
		return None

	def connection(self):
		return self.parent()

	def database(self):
		return self

	def connectionDetails(self):
		return []


	def schemasFactory(self, row, db):
		return None

	def schemas(self):
		schemas = self.connector.getSchemas()
		if schemas == None:
			return None
		return map(lambda x: self.schemasFactory(x, self), schemas)

	def tablesFactory(self, row, db, schema=None):
		return None

	def tables(self, schema=None):
		tables = self.connector.getTables(schema.name if schema else None)
		if tables == None:
			return None
		return map(lambda x: self.tablesFactory(x, self, schema), tables)


class Schema(Item):
	def __init__(self, db):
		Item.__init__(self, db)
		self.oid = self.name = self.owner = self.perms = None
		self.tableCount = 0

	def database(self):
		return self.parent()

	def tables(self):
		return self.parent().tables(self)


class Table(Item):
	def __init__(self, db, schema=None, parent=None):
		Item.__init__(self, db)
		self._schema = schema
		self.name = self.isView = self.owner = self.pages = self.geomCol = self.geomType = self.geomDim = self.srid = None
		self.rowCount = None

		self._fields = self._indexes = self._triggers = None

	def database(self):
		return self.parent()

	def schema(self):
		return self._schema


	def tableFieldsFactory(self):
		return TableField

	def fields(self):
		if self._fields == None:
			fields = self.database().connector.getTableFields(self.name, self.schema().name if self.schema() else None)
			if fields != None:
				self._fields = map(lambda x: self.tableFieldsFactory(x, self), fields)
		return self._fields

	def tableConstraintsFactory(self):
		return TableConstraint

	def constraints(self):
		if self._constraints == None:
			constraints = self.database().connector.getTableConstraints(self.name, self.schema().name if self.schema() else None)
			if constraints != None:
				self._constraints = map(lambda x: self.tableConstraintsFactory(x, self), constraints)
		return self._constraints

	def tableIndexesFactory(self):
		return TableIndex

	def indexes(self):
		if self._indexes == None:
			indexes = self.database().connector.getTableIndexes(self.name, self.schema().name if self.schema() else None)
			if indexes != None:
				self._indexes = map(lambda x: self.tableIndexesFactory(x, self), indexes)
		return self._indexes



	def spatialInfo(self):
		if self.geomType == None:
			return []

		ret = [
			("Column:", self.geomColumn),
			("Geometry:", self.geomType)
		]

		# only if we have info from geometry_columns
		if self.geomDim:
			ret.append( ("Dimension:", self.geomDim) )
			sr_info = self.database().connector.getSpatialRefInfo(self.srid) if self.srid != -1 else "Undefined"
			if sr_info: ret.append( ("Spatial ref:", "%s (%d)" % (sr_info, self.srid)) )

		# estimated extent
		if not self.isView:
			extent = self.database().connector.getTableEstimatedExtent(self.geomColumn, self.name, self.schema().name if self.schema() else None)
			if extent != None and extent[0] != None:
				extent = '%.5f, %.5f - %.5f, %.5f' % extent
			else:
				extent = '(unknown)'
			ret.append( ("Extent:", extent) )

		# is there an entry in geometry_columns?
		if self.geomType.lower() == 'geometry':
			ret.append( u"\n<warning>There isn't entry in geometry_columns!" )

		# find out whether the geometry column has spatial index on it
		if not self.isView:
			has_spatial_index = False
			for fld in self.fields():
				if fld.name == self.geomColumn:
					for idx in self.indexes():
						if fld.num in idx.columns:
							has_spatial_index = True
							break
					break

			if not has_spatial_index:
				ret.append( u'\n<warning>No spatial index defined.' )

		return ret


	def runAction(self, action):
		if action == "rows/count":
			try:
				self.rowCount = self.database().connector.getTableRowCount(self.name, self.schema().name if self.schema() else None)
				self.rowCount = int(self.rowCount) if self.rowCount != None else None
			except:
				self.rowCount = "Unknown"


class TableSubItem:
	def __init__(self, table):
		self._table = table

	def __del__(self):
		print "TableSubItem.__del__", self
		self._table = None

	def table(self):
		return self._table


class TableField(TableSubItem):
	def __init__(self, table):
		TableSubItem.__init__(self, table)
		self.num = self.name = self.dataType = self.modifier = self.notNull = self.default = self.hasDefault = self.primaryKey = None

	def definition(self):
		name = self._table.database().quoteId(self.name)
		data_type = u"%s(%s)" % (self.dataType, self.modifier) if self.modifier is not None else u"%s" % self.dataType
		not_null = "NOT NULL" if self.notNull else ""

		txt = u"%s %s %s" % (name, data_type, not_null)
		if self.hasDefault:
			txt += u" DEFAULT %s" % (self.default if self.default is not None else "NULL")
		return txt


class TableConstraint(TableSubItem):
	""" class that represents a constraint of a table (relation) """
	
	TypeCheck, TypeForeignKey, TypePrimaryKey, TypeUnique = range(4)
	types = { "c" : TypeCheck, "f" : TypeForeignKey, "p" : TypePrimaryKey, "u" : TypeUnique }
	
	onAction = { "a" : "NO ACTION", "r" : "RESTRICT", "c" : "CASCADE", "n" : "SET NULL", "d" : "SET DEFAULT" }
	matchTypes = { "u" : "UNSPECIFIED", "f" : "FULL", "p" : "PARTIAL" }

	def __init__(self, table):
		TableSubItem.__init__(self, table)
		self._table = table
		self.name = self.type = self.columns = None


class TableIndex(TableSubItem):
	def __init__(self, table):
		TableSubItem.__init__(self, table)
		self.name = self.columns = self.isUnique = None

