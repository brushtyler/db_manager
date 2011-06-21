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

from ..plugin import *
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

	def privilegesDetails(self):
		return None

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

	def spatialInfo(self):
		if self.geomType == None:
			return []

		ret = [
			("Column:", self.geomColumn),
			("Geometry:", self.geomType)
		]

		if self.geomDim: # only if we have info from geometry_columns
			ret.append( ("Dimension:", self.geomDim) )
			sr_info = self._db.connector.getSpatialRefInfo(self.srid) if self.srid != -1 else "Undefined"
			if sr_info: ret.append( ("Spatial ref:", "%s (%d)" % (sr_info, self.srid)) )

		if not self.isView:
			# estimated extent
			extent = self._db.connector.getTableEstimatedExtent(self.geomColumn, self.name, self.schema().name if self.schema() else None)
			if extent != None and extent[0] != None:
				extent = '%.5f, %.5f - %.5f, %.5f' % extent
			else:
				extent = '(unknown)'
			ret.append( ("Extent:", extent) )

		if self.geomType.lower() == 'geometry':
			ret.append( u"\n<warning>There isn't entry in geometry_columns!" )

		if not self.isView:
			# find out whether the geometry column has spatial index on it
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

	def fieldsDetails(self):
		pass


	def fields(self):
		return map(lambda x: SLTableField(x, self), self._db.connector.getTableFields(self.name))

	def indexes(self):
		if self._indexes == None:
			self._indexes = map(lambda x: SLTableIndex(x, self), self._db.connector.getTableIndexes(self.name))
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

