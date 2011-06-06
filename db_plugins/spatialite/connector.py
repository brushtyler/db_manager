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

from ...db_plugins import DBConnector, DbError
from pyspatialite import dbapi2 as sqlite

class SpatiaLiteDBConnector(DBConnector):
	def __init__(self, uri):
		DBConnector.__init__(self, uri)

		self.dbname = uri.database()
		try:
			self.con = sqlite.connect( self.__connectionInfo() )
		except sqlite.OperationalError, e:
			raise DbError(e)
		
		self.has_spatial = self.__checkSpatial()

		# a counter to ensure that the cursor will be unique
		self.last_cursor_id = 0

	def __connectionInfo(self):
		return '%s' % self.dbname
	
	def __checkSpatial(self):
		""" check if is a valid spatialite db """
		try:
			c = self.con.cursor()
			self._exec_sql(c, "SELECT CheckSpatialMetaData()")
			self.has_geometry_columns = c.fetchone()[0] == 1
		except Exception, e:
			self.has_geometry_columns = False

		self.has_geometry_columns_access = self.has_geometry_columns
		return self.has_geometry_columns
	
	def getInfo(self):
		c = self.con.cursor()
		self._exec_sql(c, "SELECT sqlite_version()")
		return c.fetchone()[0]

	def getSpatialInfo(self):
		""" returns tuple about spatialite support:
			- lib version
			- geos version
			- proj version
		"""
		c = self.con.cursor()
		self._exec_sql(c, "SELECT spatialite_version(), NULL, NULL, geos_version(), proj4_version(), NULL")
		return c.fetchone()


	def schemas(self):
		return None

	def tables(self, schema=None):
		"""
			get list of tables, whether table has geometry column(s) etc.
			
			geometry_columns:
			- f_table_name
			- f_geometry_column
			- coord_dimension
			- srid
			- type
		"""
		c = self.con.cursor()

		sys_tables = ['sqlite_stat1']
		# get the R*Tree tables
		sql = "SELECT f_table_name, f_geometry_column FROM geometry_columns WHERE spatial_index_enabled = 1"
		self._exec_sql(c, sql)		
		for idx_item in c.fetchall():
			sys_tables.append( 'idx_%s_%s' % idx_item )
			sys_tables.append( 'idx_%s_%s_node' % idx_item )
			sys_tables.append( 'idx_%s_%s_parent' % idx_item )
			sys_tables.append( 'idx_%s_%s_rowid' % idx_item )

		items = []
		# get geometry info from geometry_columns if exists
		if self.has_geometry_columns:
			sql = """SELECT m.name, m.type = 'view', g.f_geometry_column, g.type, g.coord_dimension, g.srid 
							FROM sqlite_master AS m LEFT JOIN geometry_columns AS g ON lower(m.name) = lower(g.f_table_name)
							WHERE m.type in ('table', 'view') 
							ORDER BY m.name, g.f_geometry_column"""
		else:
			sql = "SELECT name, type, NULL, NULL, NULL, NULL FROM sqlite_master WHERE type IN ('table', 'view')"

		self._exec_sql(c, sql)

		for geo_item in c.fetchall():
			item = list(geo_item)
			item.append( item[0] in sys_tables )
			items.append( item )
			
		return map(lambda x: Table(x), items)


	def _exec_sql(self, cursor, sql):
		try:
			cursor.execute(sql)
		except sqlite.Error, e:
			# do the rollback to avoid a "current transaction aborted, commands ignored" errors
			self.con.rollback()
			raise DbError(e)
		
	def _exec_sql_and_commit(self, sql):
		""" tries to execute and commit some action, on error it rolls back the change """
		c = self.con.cursor()
		self._exec_sql(c, sql)
		self.con.commit()

class Table:
	def __init__(self, row):
		self.name, self.isView, self.geomCol, self.geomType, self.geomDim, self.srid, self.sysTable = row
		self.schema = self.owner = self.tuples = self.pages = None

