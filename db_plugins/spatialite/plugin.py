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
from .connector import SpatiaLiteDBConnector

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ..plugin import DBPlugin, Database, Table, VectorTable, RasterTable, TableField, TableConstraint, TableIndex, TableTrigger
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
		return QIcon(":/db_manager/spatialite/icon")

	@classmethod
	def typeName(self):
		return 'spatialite'

	@classmethod
	def typeNameString(self):
		return 'SpatiaLite'

	@classmethod
	def providerName(self):
		return 'spatialite'

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
		return DBPlugin.connect(self, uri)


class SLDatabase(Database):
	def __init__(self, connection, uri):
		Database.__init__(self, connection, uri)

	def connectorsFactory(self, uri):
		return SpatiaLiteDBConnector(uri)


	def dataTablesFactory(self, row, db, schema=None):
		return SLTable(row, db, schema)

	def vectorTablesFactory(self, row, db, schema=None):
		return SLVectorTable(row, db, schema)

	def rasterTablesFactory(self, row, db, schema=None):
		return SLRasterTable(row, db, schema)


	def info(self):
		from .info_model import SLDatabaseInfo
		return SLDatabaseInfo(self)

	def sqlDataModel(self, sql, parent):
		from .data_model import SLSqlModel
		return SLSqlModel(self, sql, parent)


class SLTable(Table):
	def __init__(self, row, db, schema=None):
		Table.__init__(self, db, None)
		self.name, self.isView, self.isSysTable = row


	def tableFieldsFactory(self, row, table):
		return SLTableField(row, table)

	def tableIndexesFactory(self, row, table):
		return SLTableIndex(row, table)

	def tableTriggersFactory(self, row, table):
		return SLTableTrigger(row, table)


	def dataModel(self, parent):
		from .data_model import SLTableModel
		return SLTableModel(self, parent)


class SLVectorTable(SLTable, VectorTable):
	def __init__(self, row, db, schema=None):
		SLTable.__init__(self, row[:-5], db, schema)
		VectorTable.__init__(self, db, schema)
		self.geomTableName, self.geomColumn, self.geomType, self.geomDim, self.srid = row[-5:]

	def uri(self):
		uri = self.database().uri()
		pk = self.getValidQGisUniqueFields(True)
		uri.setDataSource('', self.geomTableName, self.geomColumn, QString(), pk.name if pk else QString())
		return uri

class SLRasterTable(SLTable, RasterTable):
	def __init__(self, row, db, schema=None):
		SLTable.__init__(self, row[:-3], db, schema)
		RasterTable.__init__(self, db, schema)
		self.prefixName, self.geomColumn, self.srid = row[-3:]
		self.geomType = 'RASTER'

	#def info(self):
		#from .info_model import SLRasterTableInfo
		#return SLRasterTableInfo(self)

	def gdalUri(self):
		uri = self.database().uri()
		gdalUri = u'RASTERLITE:%s,table=%s' % (uri.database(), self.prefixName)
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

