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
from .html_elems import HtmlParagraph, HtmlTable

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

	def info(self):
		from .info_model import DatabaseInfo
		return DatabaseInfo(None)


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

	def info(self):
		pass

	def runAction(self):
		pass


class Database(Item):
	def __init__(self, dbplugin, uri):
		Item.__init__(self, dbplugin)
		self.connector = self.connectorsFactory( uri )

	def connectorsFactory(self, uri):
		return None

	def connection(self):
		return self.parent()

	def database(self):
		return self


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


	def info(self):
		from .info_model import DatabaseInfo
		return DatabaseInfo(self)


class Schema(Item):
	def __init__(self, db):
		Item.__init__(self, db)
		self.oid = self.name = self.owner = self.perms = None
		self.tableCount = 0

	def database(self):
		return self.parent()

	def tables(self):
		return self.parent().tables(self)


	def info(self):
		from .info_model import SchemaInfo
		return SchemaInfo(self)


class Table(Item):
	def __init__(self, db, schema=None, parent=None):
		Item.__init__(self, db)
		self._schema = schema
		self.name = self.isView = self.owner = self.pages = self.geomCol = self.geomType = self.geomDim = self.srid = None
		self.rowCount = None

		self._fields = self._indexes = self._constraints = self._triggers = self._rules = None

	def __del__(self):
		print "Table.__del__", self
		self._fields = self._indexes = self._constraints = self._triggers = self._rules = None

	def database(self):
		return self.parent()

	def schema(self):
		return self._schema

	def schemaName(self):
		return self.schema().name if self.schema() else None

	def info(self):
		from .info_model import TableInfo
		return TableInfo(self)


	def tableFieldsFactory(self):
		return None

	def fields(self):
		if self._fields == None:
			fields = self.database().connector.getTableFields(self.name, self.schemaName())
			if fields != None:
				self._fields = map(lambda x: self.tableFieldsFactory(x, self), fields)
		return self._fields


	def tableConstraintsFactory(self):
		return None

	def constraints(self):
		if self._constraints == None:
			constraints = self.database().connector.getTableConstraints(self.name, self.schemaName())
			if constraints != None:
				self._constraints = map(lambda x: self.tableConstraintsFactory(x, self), constraints)
		return self._constraints


	def tableIndexesFactory(self):
		return None

	def indexes(self):
		if self._indexes == None:
			indexes = self.database().connector.getTableIndexes(self.name, self.schemaName())
			if indexes != None:
				self._indexes = map(lambda x: self.tableIndexesFactory(x, self), indexes)
		return self._indexes


	def tableTriggersFactory(self, row, table):
		return None

	def triggers(self):
		if self._triggers == None:
			triggers = self.database().connector.getTableTriggers(self.name, self.schemaName())
			if triggers != None:
				self._triggers = map(lambda x: self.tableTriggersFactory(x, self), triggers)
		return self._triggers


	def tableRulesFactory(self, row, table):
		return None

	def rules(self):
		if self._rules == None:
			rules = self.database().connector.getTableRules(self.name, self.schemaName())
			if rules != None:
				self._rules = map(lambda x: self.tableRulesFactory(x, self), rules)
		return self._rules


	def runAction(self, action):
		action = unicode(action)

		if action.startswith( "rows/" ):
			if action == "rows/count":
				try:
					self.rowCount = self.database().connector.getTableRowCount(self.name, self.schemaName())
					self.rowCount = int(self.rowCount) if self.rowCount != None else None
				except DbError:
					self.rowCount = "Unknown"
				return True

		elif action.startswith( "triggers/" ):
			parts = action.split('/')
			trigger_action = parts[1]

			msg = u"Do you want to %s all triggers?" % trigger_action
			if QMessageBox.question(None, "Table triggers", msg, QMessageBox.Yes|QMessageBox.No) == QMessageBox.No:
				return False

			if trigger_action == "enable" or trigger_action == "disable":
				enable = trigger_action == "enable"
				try:
					self.database().connector.enableAllTableTriggers(enable, self.name, self.schemaName())
				except DbError:
					raise
				return True

		elif action.startswith( "trigger/" ):
			parts = action.split('/')
			trigger_name = parts[1]
			trigger_action = parts[2]

			msg = u"Do you want to %s trigger %s?" % (trigger_action, trigger_name)
			if QMessageBox.question(None, "Table trigger", msg, QMessageBox.Yes|QMessageBox.No) == QMessageBox.No:
				return False

			if trigger_action == "delete":
				try:
					self.database().connector.deleteTableTrigger(trigger_name, self.name, self.schemaName())
				except DbError:
					raise
				return True

			elif trigger_action == "enable" or trigger_action == "disable":
				enable = trigger_action == "enable"
				try:
					self.database().connector.enableTableTrigger(trigger_name, enable, self.name, self.schemaName())
				except DbError:
					raise
				return True

		return False


class TableSubItem(QObject):
	def __init__(self, table):
		QObject.__init__(self, table)

	def __del__(self):
		print "TableSubItem.__del__", self

	def table(self):
		return self.parent()


class TableField(TableSubItem):
	def __init__(self, table):
		TableSubItem.__init__(self, table)
		self.num = self.name = self.dataType = self.modifier = self.notNull = self.default = self.hasDefault = self.primaryKey = None

	def type2String(self):
		if self.modifier == None or self.modifier == -1:
			return u"%s" % self.dataType
		return u"%s (%s)" % (self.dataType, self.modifier)

	def default2String(self):
		if not self.hasDefault:
			return ''
		return self.default if self.default != None else "NULL"

	def definition(self):
		name = self.table().database().quoteId(self.name)
		not_null = "NOT NULL" if self.notNull else ""

		txt = u"%s %s %s" % (name, self.type2String(), not_null)
		if self.hasDefault:
			txt += u" DEFAULT %s" % self.default2String()
		return txt


class TableConstraint(TableSubItem):
	""" class that represents a constraint of a table (relation) """
	
	TypeCheck, TypeForeignKey, TypePrimaryKey, TypeUnique = range(4)
	types = { "c" : TypeCheck, "f" : TypeForeignKey, "p" : TypePrimaryKey, "u" : TypeUnique }
	
	onAction = { "a" : "NO ACTION", "r" : "RESTRICT", "c" : "CASCADE", "n" : "SET NULL", "d" : "SET DEFAULT" }
	matchTypes = { "u" : "UNSPECIFIED", "f" : "FULL", "p" : "PARTIAL" }

	def __init__(self, table):
		TableSubItem.__init__(self, table)
		self.name = self.type = self.columns = None

	def type2String(self):
		if self.type == TableConstraint.TypeCheck: return "Check"
		if self.type == TableConstraint.TypePrimaryKey: return "Primary key"
		if self.type == TableConstraint.TypeForeignKey: return "Foreign key"
		if self.type == TableConstraint.TypeUnique: return "Unique"
		return 'Unknown'


class TableIndex(TableSubItem):
	def __init__(self, table):
		TableSubItem.__init__(self, table)
		self.name = self.columns = self.isUnique = None

class TableTrigger(TableSubItem):
	""" class that represents a trigger """
	
	# Bits within tgtype (pg_trigger.h)
	TypeRow      = (1 << 0) # row or statement
	TypeBefore   = (1 << 1) # before or after
	# events: one or more
	TypeInsert   = (1 << 2)
	TypeDelete   = (1 << 3)
	TypeUpdate   = (1 << 4)
	TypeTruncate = (1 << 5)

	def __init__(self, table):
		TableSubItem.__init__(self, table)
		self.name = self.function = None

	def type2String(self):
		trig_type = u''
		trig_type += "Before " if self.type & TableTrigger.TypeBefore else "After "
		if self.type & TableTrigger.TypeInsert: trig_type += "INSERT "
		if self.type & TableTrigger.TypeUpdate: trig_type += "UPDATE "
		if self.type & TableTrigger.TypeDelete: trig_type += "DELETE "
		if self.type & TableTrigger.TypeTruncate: trig_type += "TRUNCATE "
		trig_type += "\n"
		trig_type += "for each "
		trig_type += "row" if self.type & TableTrigger.TypeRow else "statement"
		return trig_type

class TableRule(TableSubItem):
	def __init__(self, table):
		TableSubItem.__init__(self, table)
		self.name = self.definition = None
 
