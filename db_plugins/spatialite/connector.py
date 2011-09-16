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

from ..connector import DBConnector
from ..plugin import ConnectionError, DbError, Table

from pyspatialite import dbapi2 as sqlite

def classFactory():
	return SpatiaLiteDBConnector

class SpatiaLiteDBConnector(DBConnector):
	def __init__(self, uri):
		DBConnector.__init__(self, uri)

		self.dbname = uri.database()
		if not QFile.exists( self.dbname ):
			raise ConnectionError( u'"%s" not found' % self.dbname )

		try:
			self.connection = sqlite.connect( self._connectionInfo() )
		except sqlite.OperationalError, e:
			raise ConnectionError(e)

		self._checkSpatial()
		self._checkRaster()
		self._checkGeometryColumnsTable()
		self._checkRastersTable()

	def _connectionInfo(self):
		return unicode(self.dbname)
	
	def _checkSpatial(self):
		""" check if it's a valid spatialite db """
		self.has_spatial = self._checkGeometryColumnsTable()
		return self.has_spatial

	def _checkRaster(self):
		""" check if it's a rasterite db """
		self.has_raster = self._checkRastersTable()
		return self.has_raster

	def _checkGeometryColumnsTable(self):
		try:
			c = self.connection.cursor()
			self._execute(c, u"SELECT CheckSpatialMetaData()")
			self.has_geometry_columns = c.fetchone()[0] == 1
		except Exception, e:
			self.has_geometry_columns = False

		self.has_geometry_columns_access = self.has_geometry_columns
		return self.has_geometry_columns

	def _checkRastersTable(self):
		c = self.connection.cursor()
		sql = u"SELECT count(*) = 3 FROM sqlite_master WHERE name IN ('layer_params', 'layer_statistics', 'raster_pyramids')"
		self._execute(c, sql)
		ret = c.fetchone()
		return ret and ret[0]
	
	def getInfo(self):
		c = self.connection.cursor()
		self._execute(c, u"SELECT sqlite_version()")
		return c.fetchone()

	def getSpatialInfo(self):
		""" returns tuple about spatialite support:
			- lib version
			- geos version
			- proj version
		"""
		if not self.has_spatial:
			return

		c = self.connection.cursor()
		try:
			self._execute(c, u"SELECT spatialite_version(), geos_version(), proj4_version()")
		except DbError:
			return

		return c.fetchone()


	def getSchemas(self):
		return None

	def getTables(self, schema=None):
		""" get list of tables """
		tablenames = []
		items = []

		vectors = self.getVectorTables(schema)
		for tbl in vectors:
			tablenames.append( tbl[1] )
			items.append( tbl )

		rasters = self.getRasterTables(schema)
		for tbl in rasters:
			tablenames.append( tbl[1] )
			items.append( tbl )

		c = self.connection.cursor()

		sys_tables = ['sqlite_stat1']
		if self.has_geometry_columns:
			# get the R*Tree tables
			sql = u"SELECT f_table_name, f_geometry_column FROM geometry_columns WHERE spatial_index_enabled = 1"
			self._execute(c, sql)		
			for idx_item in c.fetchall():
				sys_tables.append( 'idx_%s_%s' % idx_item )
				sys_tables.append( 'idx_%s_%s_node' % idx_item )
				sys_tables.append( 'idx_%s_%s_parent' % idx_item )
				sys_tables.append( 'idx_%s_%s_rowid' % idx_item )

			
		sql = u"SELECT name, type = 'view' FROM sqlite_master WHERE type IN ('table', 'view')"
		self._execute(c, sql)

		for tbl in c.fetchall():
			if tablenames.count( tbl[0] ) <= 0:
				item = list(tbl)
				item.insert(0, Table.TableType)
				items.append( item )

		for tbl in items:
			tbl.insert(3, tbl[1] in sys_tables)

		return sorted( items, cmp=lambda x,y: cmp(x[1], y[1]) )

	def getVectorTables(self, schema=None):
		""" get list of table with a geometry column
			it returns:
				name (table name)
				type = 'view' (is a view?)
				geometry_column:
					f_table_name (the table name in geometry_columns may be in a wrong case, use this to load the layer)
					f_geometry_column
					type 
					coord_dimension 
					srid
		"""
					
		if not self.has_geometry_columns:
			return []

		c = self.connection.cursor()
			
		# get geometry info from geometry_columns if exists
		sql = u"""SELECT m.name, m.type = 'view', g.f_table_name, g.f_geometry_column, g.type, g.coord_dimension, g.srid 
						FROM sqlite_master AS m JOIN geometry_columns AS g ON lower(m.name) = lower(g.f_table_name)
						WHERE m.type in ('table', 'view') 
						ORDER BY m.name, g.f_geometry_column"""

		self._execute(c, sql)

		items = []
		for tbl in c.fetchall():
			item = list(tbl)
			item.insert(0, Table.VectorType)
			items.append( item )

		return items


	def getRasterTables(self, schema=None):
		""" get list of table with a geometry column
			it returns:
				name (table name)
				type = 'view' (is a view?)
				geometry_column:
					r.table_name (the prefix table name, use this to load the layer)
					r.geometry_column
					srid
		"""
					
		if not self.has_geometry_columns:
			return []
		if not self.has_raster:
			return []

		c = self.connection.cursor()
			
		# get geometry info from geometry_columns if exists
		sql = u"""SELECT r.table_name||'_rasters', m.type = 'view', r.table_name, r.geometry_column, g.srid
						FROM sqlite_master AS m JOIN geometry_columns AS g ON lower(m.name) = lower(g.f_table_name) 
						JOIN layer_params AS r ON REPLACE(m.name, '_metadata', '') = r.table_name
						WHERE m.type in ('table', 'view') AND m.name = r.table_name||'_metadata'
						ORDER BY r.table_name"""

		self._execute(c, sql)

		items = []
		for i, tbl in enumerate(c.fetchall()):
			item = list(tbl)
			item.insert(0, Table.RasterType)
			items.append( item )
			
		return items

	def getTableRowCount(self, table, schema=None):
		c = self.connection.cursor()
		self._execute(c, u"SELECT COUNT(*) FROM %s" % self.quoteId(table) )
		return c.fetchone()[0]

	def getTableFields(self, table, schema=None):
		""" return list of columns in table """
		c = self.connection.cursor()
		sql = u"PRAGMA table_info(%s)" % (self.quoteId(table))
		self._execute(c, sql)
		return c.fetchall()

	def getTableIndexes(self, table, schema=None):
		""" get info about table's indexes """
		c = self.connection.cursor()
		sql = u"PRAGMA index_list(%s)" % (self.quoteId(table))
		self._execute(c, sql)
		indexes = c.fetchall()

		for i, idx in enumerate(indexes):
			num, name, unique = idx
			sql = u"PRAGMA index_info(%s)" % (self.quoteId(name))
			self._execute(c, sql)

			idx = [num, name, unique]
			cols = []
			for seq, cid, cname in c.fetchall():
				cols.append(cid)
			idx.append(cols)
			indexes[i] = idx

		return indexes

	def getTableConstraints(self, table, schema=None):
		return None

	def getTableTriggers(self, table, schema=None):
		c = self.connection.cursor()
		sql = u"SELECT name, sql FROM sqlite_master WHERE lower(tbl_name) = lower(%s) AND type = 'trigger'" % (self.quoteString(table))
		self._execute(c, sql)
		return c.fetchall()

	def deleteTableTrigger(self, trigger, table=None, schema=None):
		""" delete trigger """
		sql = u"DROP TRIGGER %s" % self.quoteId(trigger)
		self._execute_and_commit(sql)


	def getTableEstimatedExtent(self, geom, table, schema=None):
		""" find out estimated extent (from the statistics) """
		c = self.connection.cursor()

		if self.isRasterTable(table, schema):
			table = QString(table).replace('_rasters', '_metadata')
			geom = u'geometry'

		sql = u"""SELECT Min(MbrMinX(%(geom)s)), Min(MbrMinY(%(geom)s)), Max(MbrMaxX(%(geom)s)), Max(MbrMaxY(%(geom)s)) 
						FROM %(table)s """ % { 'geom' : self.quoteId(geom), 'table' : self.quoteId(table) }
		try:
			self._execute(c, sql)
		except DbError, e:
			return
		return c.fetchone()
	
	def getViewDefinition(self, view, schema=None):
		""" returns definition of the view """
		sql = u"SELECT sql FROM sqlite_master WHERE type = 'view' AND name = %s" % self.quoteString(view)
		c = self.connection.cursor()
		self._execute(c, sql)
		return c.fetchone()[0]

	def getSpatialRefInfo(self, srid):
		sql = u"SELECT ref_sys_name FROM spatial_ref_sys WHERE srid = %s" % self.quoteString(srid)
		c = self.connection.cursor()
		self._execute(c, sql)
		return c.fetchone()[0]


	def createTable(self, table, fields, pkey=None, schema=None):
		""" create ordinary table
				'fields' is array containing instances of TableField
				'pkey' contains name of column to be used as primary key
		"""
		if len(fields) == 0:
			return False
		
		sql = u"CREATE TABLE %s (" % self.quoteId(table)
		sql += u", ".join( map(lambda x: x.definition(), fields) )
		if pkey:
			sql += u", PRIMARY KEY (%s)" % self.quoteId(pkey)
		sql += ")"

		self._execute_and_commit(sql)
		return True

	def isVectorTable(self, table, schema=None):
		if self.has_geometry_columns:
			c = self.connection.cursor()
			sql = u"SELECT count(*) FROM geometry_columns WHERE f_table_name = %s" % self.quoteString(table)
			self._execute(c, sql)
			return c.fetchone()[0] > 0
		return True

	def isRasterTable(self, table, schema=None):
		if self.has_geometry_columns and self.has_raster:
			if not QString(table).endsWith( "_rasters" ):
				return False

			c = self.connection.cursor()
			sql = u"""SELECT count(*) 
					FROM layer_params AS r JOIN geometry_columns AS g 
						ON r.table_name||'_metadata' = g.f_table_name
					WHERE r.table_name = REPLACE(%s, '_rasters', '')""" % self.quoteString(table)
			self._execute(c, sql)
			return c.fetchone()[0] > 0
		return False

	def deleteTable(self, table, schema=None):
		""" delete table from the database """
		if self.isRasterTable(table, schema):
			return False

		c = self.connection.cursor()
		sql = u"DROP TABLE %s" % self.quoteId(table)
		self._execute(c, sql)
		sql = u"DELETE FROM geometry_columns WHERE lower(f_table_name) = lower(%s)" % self.quoteString(table)
		self._execute(c, sql)
		self.connection.commit()


	def emptyTable(self, table, schema=None):
		""" delete all rows from table """
		if self.isRasterTable(table, schema):
			return False

		sql = u"DELETE FROM %s" % self.quoteId(table)
		self._execute_and_commit(sql)
		
	def renameTable(self, table, new_table, schema=None):
		""" rename a table """
		if new_table == table:
			return

		if self.isRasterTable(table, schema):
			return False

		c = self.connection.cursor()

		sql = u"ALTER TABLE %s RENAME TO %s" % (self.quoteId(table), self.quoteId(new_table))
		self._execute(c, sql)
		
		# update geometry_columns
		if self.has_geometry_columns:
			sql = u"UPDATE geometry_columns SET f_table_name=%s WHERE f_table_name=%s" % (self.quoteString(new_table), self.quoteString(table))
			self._execute(c, sql)

		self.connection.commit()

	def moveTable(self, table, new_table, schema=None, new_schema=None):
		return self.renameTable(table, new_table)
		
	def createView(self, name, query, schema=None):
		sql = u"CREATE VIEW %s AS %s" % (self.quoteId(name), query)
		self._execute_and_commit(sql)
	
	def deleteView(self, name, schema=None):
		sql = u"DROP VIEW %s" % self.quoteId(name)
		self._execute_and_commit(sql)
		return True
	
	def renameView(self, name, new_name, schema=None):
		""" rename view """
		return self.renameTable(name, new_name)

	def hasCustomQuerySupport(self):
		from qgis.core import QGis
		return QGis.QGIS_VERSION[0:3] >= "1.6"

	def fieldTypes(self):
		return [
			"integer", "bigint", "smallint", # integers
			"real", "double", "float", "numeric", # floats
			"varchar(n)", "character(n)", "text", # strings
			"date", "datetime" # date/time
		]


	def _execute(self, cursor, sql):
		try:
			cursor.execute(unicode(sql))
		except sqlite.OperationalError, e:
			# do the rollback to avoid a "current transaction aborted, commands ignored" errors
			self.connection.rollback()
			raise DbError(e, sql)
		
	def _execute_and_commit(self, sql):
		""" tries to execute and commit some action, on error it rolls back the change """
		c = self.connection.cursor()
		self._execute(c, sql)
		self.connection.commit()

	def _get_cursor(self, name=None):
		if name:
			name = QString( unicode(name).encode('ascii', 'replace') ).replace( QRegExp("\W"), "_" ).toAscii()
			self._last_cursor_named_id = 0 if not hasattr(self, '_last_cursor_named_id') else self._last_cursor_named_id + 1
			return self.connection.cursor( "%s_%d" % (name, self._last_cursor_named_id) )
		return self.connection.cursor()

	def _fetchall(self, c):
		try:
			return c.fetchall()
		except sqlite.OperationalError, e:
			# do the rollback to avoid a "current transaction aborted, commands ignored" errors
			self.connection.rollback()
			raise DbError(e)

	def _commit(self):
		self.connection.commit()

	def _rollback(self):
		self.connection.rollback()

	def _get_columns(self, c):
		if c.description:
			return map(lambda x: x[0], c.description)
		return []

