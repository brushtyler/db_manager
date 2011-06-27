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

from ..plugin import DBPlugin, Database, Table, TableField, TableConstraint, TableIndex
try:
	from . import resources_rc
except ImportError:
	pass


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


	def connect(self, parent=None):
		conn_name = self.connectionName()
		settings = QSettings()
		settings.beginGroup( u"/%s/%s" % (self.connectionSettingsKey(), conn_name) )

		if not settings.contains( "sqlitepath" ): # non-existent entry?
			raise InvalidDataException( 'there is no defined database connection "%s".' % conn_name )

		database = unicode(settings.value("sqlitepath").toString())

		import qgis.core
		from .connector import SpatiaLiteDBConnector
		uri = qgis.core.QgsDataSourceURI()
		uri.setDatabase(database)
		self.db = SLDatabase( self, SpatiaLiteDBConnector(uri) )
		return True


class SLDatabase(Database):
	def __init__(self, connection, connector):
		Database.__init__(self, connection, connector)

	def connectionDetails(self):
		return [ 
			("Filename:", self.connector.dbname) 
		]

	def spatialInfo(self):
		info = self.connector.getSpatialInfo()
		ret = [
			("Library:", info[0]), 
			("GEOS:", info[1]), 
			("Proj:", info[2]) 
		]

		if not self.connector.has_geometry_columns:
			ret.append( u"\n<warning> geometry_columns table doesn't exist! " \
				"This table is essential for many GIS applications for enumeration of tables." )

		return ret

	def generalInfo(self):
		info = self.connector.getInfo()
		return [
			("SQLite version", info[0])
		]

	def tables(self, schema=None):
		return map(lambda x: SLTable(x, self), self.connector.getTables())


class SLTable(Table):
	def __init__(self, row, db, schema=None):
		Table.__init__(self, db, None)
		self.name, self.isView, self.geomColumn, self.geomType, self.geomDim, self.srid, self.isSysTable = row

	def generalInfo(self):
		if self.rowCount == None:
			self.runAction("rows/count")

		return [
			("Relation type:", "View" if self.isView else "Table"), 
			("Rows:", self.rowCount) 
		]


	def fieldsDetails(self):
		pass


	def fields(self):
		return map(lambda x: SLTableField(x, self), self.database().connector.getTableFields(self.name))

	def indexes(self):
		if self._indexes == None:
			self._indexes = map(lambda x: SLTableIndex(x, self), self.database().connector.getTableIndexes(self.name))
		return self._indexes


class SLTableField(TableField):
	def __init__(self, row, table):
		TableField.__init__(self, table)
		self.num, self.name, self.dataType, self.notNull, self.default, self.primaryKey = row
		self.hasDefault = self.default != None


class SLTableIndex(TableIndex):
	def __init__(self, row, table):
		TableIndex.__init__(self, table)
		self.num, self.name, self.isUnique, self.columns = row

