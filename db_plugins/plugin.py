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


class DBPlugin:
	def __init__(self, conn_name):
		self.connName = conn_name
		self.db = None

	def __del__(self):
		print "DBPlugin.__del__", self.connName
		self.db = None

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


class Item:
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
	def __init__(self, connection, connector):
		self.connection = connection
		self.connector = connector

	def __del__(self):
		print "Database.__del__", self.connection.connectionName()
		self.connection = None
		self.connector = None

	def connectionDetails(self):
		return []

	def database(self):
		return self

	def schemas(self):
		return None

	def tables(self, schema=None):
		return None



class DatabaseSubItem(Item):
	def __init__(self, db):
		self._db = db

	def __del__(self):
		print "DatabaseSubItem.__del__", self
		self._db = None

	def database(self):
		return self._db


class Schema(DatabaseSubItem):
	def __init__(self, db):
		DatabaseSubItem.__init__(self, db)
		self.oid = self.name = self.owner = self.perms = None
		self.tableCount = 0

	def __del__(self):
		print "Schema.__del__", self.name

	def tables(self):
		return self._db.tables(self)


class SchemaSubItem(Item):
	def __init__(self, schema):
		self._schema = schema

	def __del__(self):
		print "SchemaSubItem.__del__", self
		self._schema = None

	def schema(self):
		return self._schema


class Table(DatabaseSubItem, SchemaSubItem):
	def __init__(self, db, schema=None):
		DatabaseSubItem.__init__(self, db)
		SchemaSubItem.__init__(self, schema)
		self.name = self.isView = self.owner = self.pages = self.geomCol = self.geomType = self.geomDim = self.srid = None
		self.rowCount = None

		self._fields = self._indexes = self._triggers = None

	def __del__(self):
		print "Table.__del__", self.name
		self._db = None
		self._schema = None

	def fields(self):
		return self._fields

	def indexes(self):
		return self._indexes

	def triggers(self):
		return self._triggers


	def runAction(self, action):
		if action == "rows/count":
			try:
				self.rowCount = self._db.connector.getTableRowCount(self.name, self._schema.name if self._schema else None)
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
		self.num = self.name = self.dataType = self.notNull = self.default = self.hasDefault = self.primaryKey = None


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

