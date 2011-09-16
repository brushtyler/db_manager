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

# this will disable the dbplugin if the connector raise an ImportError
from .connector import PostGisDBConnector

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ..plugin import ConnectionError, DBPlugin, Database, Schema, Table, VectorTable, RasterTable, TableField, TableConstraint, TableIndex, TableTrigger, TableRule
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
		return QIcon(":/db_manager/postgis/icon")

	@classmethod
	def typeName(self):
		return 'postgis'

	@classmethod
	def typeNameString(self):
		return 'PostGIS'

	@classmethod
	def providerName(self):
		return 'postgres'

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
			raise InvalidDataException( u'there is no defined database connection "%s".' % conn_name )

		from qgis.core import QgsDataSourceURI
		uri = QgsDataSourceURI()
	
		get_value_str = lambda x: settings.value(x).toString()
		host, port, database, username, password = map(get_value_str, ["host", "port", "database", "username", "password"])

		# qgis1.5 use 'savePassword' instead of 'save' setting
		savedPassword = settings.value("save", False).toBool() or settings.value("savePassword", False).toBool()

		useEstimatedMetadata = settings.value("estimatedMetadata", False).toBool()
		sslmode = settings.value("sslmode", QgsDataSourceURI.SSLprefer).toInt()[0]

		settings.endGroup()

		uri.setConnection(host, port, database, username, password, sslmode)
		uri.setUseEstimatedMetadata(useEstimatedMetadata)

		err = QString()
		try:
			return DBPlugin.connect(self, uri)
		except ConnectionError, e:
			err = QString( str(e) )

		hasCredentialDlg = True
		try:
			from qgis.gui import QgsCredentials
		except ImportError:	# no credential dialog
			hasCredentialDlg = False

		# ask for valid credentials
		max_attempts = 3
		for i in range(max_attempts):
			if hasCredentialDlg:
				(ok, username, password) = QgsCredentials.instance().get(uri.connectionInfo(), username, password, err)
			else:
				(password, ok) = QInputDialog.getText(parent, u"Enter password", u'Enter password for connection "%s":' % conn_name, QLineEdit.Password)

			if not ok:
				return False

			uri.setConnection(host, port, database, username, password, sslmode)

			try:
				DBPlugin.connect(self, uri)
			except ConnectionError, e:
				if i == max_attempts-1:	# failed the last attempt
					raise e
				err = QString( str(e) )
				continue

			if hasCredentialDlg:
				QgsCredentials.instance().put(uri.connectionInfo(), username, password)
			return True

		return False


class PGDatabase(Database):
	def __init__(self, connection, uri):
		Database.__init__(self, connection, uri)

	def connectorsFactory(self, uri):
		return PostGisDBConnector(uri)


	def dataTablesFactory(self, row, db, schema=None):
		return PGTable(row, db, schema)

	def vectorTablesFactory(self, row, db, schema=None):
		return PGVectorTable(row, db, schema)

	def rasterTablesFactory(self, row, db, schema=None):
		return PGRasterTable(row, db, schema)

	def schemasFactory(self, row, db):
		return PGSchema(row, db)


	def sqlDataModel(self, sql, parent):
		from .data_model import PGSqlModel
		return PGSqlModel(self, sql, parent)


class PGSchema(Schema):
	def __init__(self, row, db):
		Schema.__init__(self, db)
		self.oid, self.name, self.owner, self.perms = row
		self.tableCount = len(self.tables())


class PGTable(Table):
	def __init__(self, row, db, schema=None):
		Table.__init__(self, db, schema)
		self.name, schema_name, self.isView, self.owner, self.estimatedRowCount, self.pages = row
		self.estimatedRowCount = int(self.estimatedRowCount)

	def runVacuumAnalyze(self):
		self.database().connector.runVacuumAnalyze(self.name, self.schemaName())


	def runAction(self, action):
		action = unicode(action)

		if action.startswith( "table/" ):
			if action == "table/vacuum":
				self.runVacuumAnalyze()
				return True

		elif action.startswith( "rule/" ):
			parts = action.split('/')
			rule_name = parts[1]
			rule_action = parts[2]

			msg = u"Do you want to %s rule %s?" % (rule_action, rule_name)
			if QMessageBox.question(None, "Table rule", msg, QMessageBox.Yes|QMessageBox.No) == QMessageBox.No:
				return False

			if rule_action == "delete":
				self.database().connector.deleteTableRule(rule_name, self.name, self.schemaName())
				self._rules = None	# refresh rules
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

	def dataModel(self, parent):
		from .data_model import PGTableModel
		return PGTableModel(self, parent)


class PGVectorTable(PGTable, VectorTable):
	def __init__(self, row, db, schema=None):
		PGTable.__init__(self, row[:-4], db, schema)
		VectorTable.__init__(self, db, schema)
		self.geomColumn, self.geomType, self.geomDim, self.srid = row[-4:]

	def info(self):
		from .info_model import PGVectorTableInfo
		return PGVectorTableInfo(self)

class PGRasterTable(PGTable, RasterTable):
	def __init__(self, row, db, schema=None):
		PGTable.__init__(self, row[:-6], db, schema)
		RasterTable.__init__(self, db, schema)
		self.geomColumn, self.pixelType, self.pixelSizeX, self.pixelSizeY, self.isExternal, self.srid = row[-6:]
		self.geomType = 'RASTER'

	def info(self):
		from .info_model import PGRasterTableInfo
		return PGRasterTableInfo(self)

	def gdalUri(self):
		uri = self.database().uri()
		schema = ( u'schema=%s' % self.schemaName() ) if self.schemaName() else ''
		gdalUri = u'PG: dbname=%s host=%s user=%s password=%s port=%s mode=2 %s table=%s' % (uri.database(), uri.host(), uri.username(), uri.password(), uri.port(), schema, self.name)
		return QString( gdalUri )

	def mimeUri(self):
		uri = u"raster:gdal:%s:%s" % (self.name, self.gdalUri())
		return QString( uri )
	
	def toMapLayer(self):
		from qgis.core import QgsRasterLayer 
		rl = QgsRasterLayer(self.gdalUri(), self.name)
		if rl.isValid():
			rl.setContrastEnhancementAlgorithm("StretchToMinimumMaximum")
		return rl

class PGTableField(TableField):
	def __init__(self, row, table):
		TableField.__init__(self, table)
		self.num, self.name, self.dataType, self.charMaxLen, self.modifier, self.notNull, self.hasDefault, self.default, typeStr = row
		self.primaryKey = False

		# convert the modifier to string (e.g. "precision,scale")
		if self.modifier != None and self.modifier != -1:
			if self.dataType in ["numeric", "geometry"]:
				if typeStr.startswith( "%s(" % self.dataType ):
					self.modifier = typeStr[ len(self.dataType)+1 : -1 ]
				else:
					self.modifier = None

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

class PGTableRule(TableRule):
	def __init__(self, row, table):
		TableRule.__init__(self, table)
		self.name, self.definition = row


