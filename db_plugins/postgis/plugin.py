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

from ..plugin import DBPlugin, Database, Schema, Table, TableField, TableConstraint, TableIndex, TableTrigger, TableRule
try:
	from . import resources_rc
except ImportError:
	pass

from ..html_elems import HtmlParagraph, HtmlList, HtmlTable


def classFactory():
	return PostGisDBPlugin

class PostGisDBPlugin(DBPlugin):

	@classmethod
	def icon(self):
		return QIcon(":/icons/postgis_elephant.png")

	@classmethod
	def typeName(self):
		return 'postgis'

	@classmethod
	def typeNameString(self):
		return 'PostGIS'

	@classmethod
	def connectionSettingsKey(self):
		return '/PostgreSQL/connections'

	def databasesFactory(self, connection, uri):
		return PGDatabase(connection, uri)

	def connect(self, parent=None):
		conn_name = self.connectionName()
		settings = QSettings()
		settings.beginGroup( u"/%s/%s" % (self.connectionSettingsKey(), conn_name) )

		if not settings.contains( "database" ): # non-existent entry?
			raise InvalidDataException( 'there is no defined database connection "%s".' % conn_name )
	
		get_value_str = lambda x: unicode(settings.value(x).toString())
		host, port, database, username, password = map(get_value_str, ["host", "port", "database", "username", "password"])

		# qgis1.5 use 'savePassword' instead of 'save' setting
		if not ( settings.value("save").toBool() or settings.value("savePassword").toBool() ):
			#dlg = qgis.gui.QgsCredentialDialog(parent)
			#(ok, username, password) = dlg.request(selected)
			(password, ok) = QInputDialog.getText(parent, "Enter password", 'Enter password for connection "%s":' % conn_name, QLineEdit.Password)
			if not ok: return False

		settings.endGroup()

		import qgis.core
		uri = qgis.core.QgsDataSourceURI()
		uri.setConnection(host, port, database, username, password)
		self.db = self.databasesFactory( self, uri )
		return True


class PGDatabase(Database):
	def __init__(self, connection, uri):
		Database.__init__(self, connection, uri)

	def connectorsFactory(self, uri):
		from .connector import PostGisDBConnector
		return PostGisDBConnector(uri)


	def tablesFactory(self, row, db, schema=None):
		return PGTable(row, db, schema)

	def schemasFactory(self, row, db):
		return PGSchema(row, db)


class PGSchema(Schema):
	def __init__(self, row, db):
		Schema.__init__(self, db)
		self.oid, self.name, self.owner, self.perms = row
		self.tableCount = len(self.tables())


class PGTable(Table):
	def __init__(self, row, db, schema=None):
		Table.__init__(self, db, schema)
		self.name, schema_name, self.isView, self.owner, self.estimatedRowCount, self.pages, self.geomColumn, self.geomType, self.geomDim, self.srid = row
		self.estimatedRowCount = int(self.estimatedRowCount)


	def runVacuumAnalyze(self):
		self.database().connector.runVacuumAnalyze(self.name, self.schemaName())


	def runAction(self, action):
		action = unicode(action)

		if action.startswith( "table/" ):
			if action == "table/vacuum":
				try:
					self.runVacuumAnalyze()
				except DbError:
					raise
				return True

		elif action.startswith( "rule/" ):
			parts = action.split('/')
			rule_name = parts[1]
			rule_action = parts[2]

			msg = u"Do you want to %s rule %s?" % (rule_action, rule_name)
			if QMessageBox.question(None, "Table rule", msg, QMessageBox.Yes|QMessageBox.No) == QMessageBox.No:
				return False

			if rule_action == "delete":
				try:
					self.database().connector.deleteTableRule(rule_name, self.name, self.schemaName())
				except DbError:
					raise
				return True

		return Table.runAction(self, action)

	def tableFieldsFactory(self, row, table):
		return PGTableField(row, table)

	def tableConstraintsFactory(self, row, table):
		return PGTableConstraint(row, table)

	def tableIndexesFactory(self, row, table):
		return PGTableIndex(row, table)

	def tableTriggersFactory(self, row, table):
		return PGTableTrigger(row, table)

	def tableRulesFactory(self, row, table):
		return PGTableRule(row, table)


	def info(self):
		from .info_model import PGTableInfo
		return PGTableInfo(self)


class PGTableField(TableField):
	def __init__(self, row, table):
		TableField.__init__(self, table)
		self.num, self.name, self.dataType, self.charMaxLen, self.modifier, self.notNull, self.hasDefault, self.default = row
		self.primaryKey = False

		# find out whether fields are part of primary key
		for con in self.table().constraints():
			if con.type == TableConstraint.TypePrimaryKey and self.num in con.columns:
				self.primaryKey = True
				break


class PGTableConstraint(TableConstraint):
	def __init__(self, row, table):
		TableConstraint.__init__(self, table)
		self.name, constr_type, self.isDefferable, self.isDeffered, columns = row[:5]
		self.columns = map(int, columns.split(' '))
		self.type = TableConstraint.types[constr_type]   # convert to enum

		if self.type == TableConstraint.TypeCheck:
			self.checkSource = row[5]
		elif self.type == TableConstraint.TypeForeignKey:
			self.foreignTable = row[6]
			self.foreignOnUpdate = TableConstraint.onAction[row[7]]
			self.foreignOnDelete = TableConstraint.onAction[row[8]]
			self.foreignMatchType = TableConstraint.matchTypes[row[9]]
			self.foreignKeys = row[10]


class PGTableIndex(TableIndex):
	def __init__(self, row, table):
		TableIndex.__init__(self, table)
		self.name, columns, self.isUnique = row
		self.columns = map(int, columns.split(' '))


class PGTableTrigger(TableTrigger):
	def __init__(self, row, table):
		TableTrigger.__init__(self, table)
		self.name, self.function, self.type, self.enabled = row

class PGTableRules(TableRule):
	def __init__(self, row, table):
		TableSubItem.__init__(self, table)
		self.name, self.definition = row


