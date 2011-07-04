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

from ..plugin import DBPlugin, Database, Table, TableField, TableConstraint, TableIndex, TableTrigger
try:
	from . import resources_rc
except ImportError:
	pass

from ..html_elems import HtmlParagraph, HtmlTable


def classFactory():
	return SpatiaLiteDBPlugin

class SpatiaLiteDBPlugin(DBPlugin):

	@classmethod
	def icon(self):
		return QIcon(":/icons/spatialite_icon.png")

	@classmethod
	def typeName(self):
		return 'spatialite'

	@classmethod
	def typeNameString(self):
		return 'SpatiaLite'

	@classmethod
	def connectionSettingsKey(self):
		return '/SpatiaLite/connections'

	def databasesFactory(self, connection, uri):
		return SLDatabase(connection, uri)

	def connect(self, parent=None):
		conn_name = self.connectionName()
		settings = QSettings()
		settings.beginGroup( u"/%s/%s" % (self.connectionSettingsKey(), conn_name) )

		if not settings.contains( "sqlitepath" ): # non-existent entry?
			raise InvalidDataException( 'there is no defined database connection "%s".' % conn_name )

		database = unicode(settings.value("sqlitepath").toString())

		import qgis.core
		uri = qgis.core.QgsDataSourceURI()
		uri.setDatabase(database)
		self.db = self.databasesFactory( self, uri )
		return True


class SLDatabase(Database):
	def __init__(self, connection, uri):
		Database.__init__(self, connection, uri)

	def connectorsFactory(self, uri):
		from .connector import SpatiaLiteDBConnector
		return SpatiaLiteDBConnector(uri)


	def schemasFactory(self, row, db):
		return None

	def tablesFactory(self, row, db, schema=None):
		return SLTable(row, db, schema)


	def info(self):
		from .info_model import SLDatabaseInfo
		return SLDatabaseInfo(self)


class SLTable(Table):
	def __init__(self, row, db, schema=None):
		Table.__init__(self, db, None)
		self.name, self.isView, self.geomColumn, self.geomType, self.geomDim, self.srid, self.isSysTable = row


	def tableFieldsFactory(self, row, table):
		return SLTableField(row, table)

	def tableIndexesFactory(self, row, table):
		return SLTableIndex(row, table)

	def tableTriggersFactory(self, row, table):
		return SLTableTrigger(row, table)


class SLTableField(TableField):
	def __init__(self, row, table):
		TableField.__init__(self, table)
		self.num, self.name, self.dataType, self.notNull, self.default, self.primaryKey = row
		self.hasDefault = self.default != None

class SLTableIndex(TableIndex):
	def __init__(self, row, table):
		TableIndex.__init__(self, table)
		self.num, self.name, self.isUnique, self.columns = row

class SLTableTrigger(TableTrigger):
	def __init__(self, row, table):
		TableTrigger.__init__(self, table)
		self.name, self.function = row

