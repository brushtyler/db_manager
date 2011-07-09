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

from ..connector import DBConnector, SqlTableModel
from ..plugin import ConnectionError, DbError

from pyspatialite import dbapi2 as sqlite

def classFactory():
	return SpatiaLiteDBConnector

class SpatiaLiteDBConnector(DBConnector):
	def __init__(self, uri):
		DBConnector.__init__(self, uri)

		self.dbname = uri.database()
		try:
			self.connection = sqlite.connect( self._connectionInfo() )
		except sqlite.OperationalError, e:
			raise ConnectionError(e)

		self._checkSpatial()
		self._checkGeometryColumnsTable()

	def _connectionInfo(self):
		return '%s' % self.dbname
	
	def _checkSpatial(self):
		""" check if is a valid spatialite db """
		self.has_spatial = self._checkGeometryColumnsTable()
		return self.has_spatial

	def _checkGeometryColumnsTable(self):
		try:
			c = self.connection.cursor()
			self._exec_sql(c, u"SELECT CheckSpatialMetaData()")
			self.has_geometry_columns = c.fetchone()[0] == 1
		except Exception, e:
			self.has_geometry_columns = False

		self.has_geometry_columns_access = self.has_geometry_columns
		return self.has_geometry_columns
	
	def getInfo(self):
		c = self.connection.cursor()
		self._exec_sql(c, u"SELECT sqlite_version()")
		return c.fetchone()

	def getSpatialInfo(self):
		""" returns tuple about spatialite support:
			- lib version
			- geos version
			- proj version
		"""
		c = self.connection.cursor()
		self._exec_sql(c, u"SELECT spatialite_version(), geos_version(), proj4_version()")
		return c.fetchone()


	def getSchemas(self):
		return None

	def getTables(self, schema=None):
		"""
			get list of tables, whether table has geometry column(s) etc.
			
			geometry_columns:
			- f_table_name
			- f_geometry_column
			- coord_dimension
			- srid
			- type
		"""
		c = self.connection.cursor()

		items = []
		sys_tables = ['sqlite_stat1']

		if self.has_geometry_columns:
			# get the R*Tree tables
			sql = u"SELECT f_table_name, f_geometry_column FROM geometry_columns WHERE spatial_index_enabled = 1"
			self._exec_sql(c, sql)		
			for idx_item in c.fetchall():
				sys_tables.append( 'idx_%s_%s' % idx_item )
				sys_tables.append( 'idx_%s_%s_node' % idx_item )
				sys_tables.append( 'idx_%s_%s_parent' % idx_item )
				sys_tables.append( 'idx_%s_%s_rowid' % idx_item )

			# get geometry info from geometry_columns if exists
			sql = u"""SELECT m.name, m.type = 'view', g.f_geometry_column, g.type, g.coord_dimension, g.srid 
							FROM sqlite_master AS m LEFT JOIN geometry_columns AS g ON lower(m.name) = lower(g.f_table_name)
							WHERE m.type in ('table', 'view') 
							ORDER BY m.name, g.f_geometry_column"""
		else:
			sql = u"SELECT name, type = 'view', NULL, NULL, NULL, NULL FROM sqlite_master WHERE type IN ('table', 'view')"

		self._exec_sql(c, sql)

		for geo_item in c.fetchall():
			item = list(geo_item)
			item.append( item[0] in sys_tables )
			items.append( item )
			
		return items


	def getTableRowCount(self, table, schema=None):
		c = self.connection.cursor()
		self._exec_sql(c, u"SELECT COUNT(*) FROM %s" % self.quoteId(table) )
		return c.fetchone()[0]

	def getTableFields(self, table, schema=None):
		""" return list of columns in table """
		c = self.connection.cursor()
		sql = u"PRAGMA table_info(%s)" % (self.quoteId(table))
		self._exec_sql(c, sql)
		return c.fetchall()

	def getTableIndexes(self, table, schema=None):
		""" get info about table's indexes """
		c = self.connection.cursor()
		sql = u"PRAGMA index_list(%s)" % (self.quoteId(table))
		self._exec_sql(c, sql)
		indexes = c.fetchall()

		for i, idx in enumerate(indexes):
			num, name, unique = idx
			sql = u"PRAGMA index_info(%s)" % (self.quoteId(name))
			self._exec_sql(c, sql)

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
		self._exec_sql(c, sql)
		return c.fetchall()

	def deleteTableTrigger(self, trigger, table=None, schema=None):
		""" delete trigger """
		sql = u"DROP TRIGGER %s" % self.quoteId(trigger)
		self._exec_sql_and_commit(sql)


	def getTableEstimatedExtent(self, geom, table, schema=None):
		""" find out estimated extent (from the statistics) """
		c = self.connection.cursor()
		sql = u"""SELECT Min(MbrMinX(%(geom)s)), Min(MbrMinY(%(geom)s)), Max(MbrMaxX(%(geom)s)), Max(MbrMaxY(%(geom)s)) 
						FROM %(table)s """ % { 'geom' : self.quoteId(geom), 'table' : self.quoteId(table) }
		self._exec_sql(c, sql)
		return c.fetchone()
	
	def getViewDefinition(self, view, schema=None):
		""" returns definition of the view """
		sql = u"SELECT sql FROM sqlite_master WHERE type = 'view' AND name = %s" % self.quoteString(view)
		c = self.connection.cursor()
		self._exec_sql(c, sql)
		return c.fetchone()[0]

	def getSpatialRefInfo(self, srid):
		sql = u"SELECT ref_sys_name FROM spatial_ref_sys WHERE srid = %s" % self.quoteString(srid)
		c = self.connection.cursor()
		self._exec_sql(c, sql)
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

		self._exec_sql_and_commit(sql)
		return True

	def deleteTable(self, table, schema=None):
		""" delete table from the database """
		sql = u"DROP TABLE %s" % self.quoteId(table)
		self._exec_sql_and_commit(sql)

	def emptyTable(self, table, schema=None):
		""" delete all rows from table """
		sql = u"DELETE FROM %s" % self.quoteId(table)
		self._exec_sql_and_commit(sql)
		
	def renameTable(self, table, new_table, schema=None):
		""" rename a table """
		if new_table == table:
			return
		c = self.connection.cursor()

		sql = u"ALTER TABLE %s RENAME TO %s" % (self.quoteId(table), self.quoteId(new_table))
		self._exec_sql(c, sql)
		
		# update geometry_columns
		if self.has_geometry_columns:
			sql = u"UPDATE geometry_columns SET f_table_name=%s WHERE f_table_name=%s" % (self.quoteString(new_table), self.quoteString(table))
			self._exec_sql(c, sql)

		self.connection.commit()

	def moveTable(self, table, new_table, schema=None, new_schema=None):
		self.renameTable(table, new_table)
		
	def createView(self, name, query, schema=None):
		sql = u"CREATE VIEW %s AS %s" % (self.quoteId(name), query)
		self._exec_sql_and_commit(sql)
	
	def deleteView(self, name, schema=None):
		sql = u"DROP VIEW %s" % self.quoteId(name)
		self._exec_sql_and_commit(sql)
	
	def renameView(self, name, new_name, schema=None):
		""" rename view """
		self.renameTable(name, new_name)

	def hasCustomQuerySupport(self):
		return True

	def fieldTypes(self):
		return [
			"integer", "bigint", "smallint", # integers
			"real", "double", "float", "numeric", # floats
			"varchar(n)", "character(n)", "text", # strings
			"date", "datetime" # date/time
		]


	def _exec_sql(self, cursor, sql):
		try:
			cursor.execute(unicode(sql))
		except sqlite.Error, e:
			# do the rollback to avoid a "current transaction aborted, commands ignored" errors
			self.connection.rollback()
			raise DbError(e, sql)
		
	def _exec_sql_and_commit(self, sql):
		""" tries to execute and commit some action, on error it rolls back the change """
		c = self.connection.cursor()
		self._exec_sql(c, sql)
		self.connection.commit()


	def getSqlTableModel(self, sql, parent):
		try:
			c = self.connection.cursor()
			t = QTime()
			t.start()
			self._exec_sql(c, sql)
			secs = t.elapsed() / 1000.0
			model = SLSqlTableModel(c, parent)
			rowcount = c.rowcount
			
			# commit before closing the cursor to make sure that the changes are stored
			self.connection.commit()
			c.close()
		except:
			raise
		return (model, secs, rowcount)


class SLSqlTableModel(SqlTableModel):	
	def __init__(self, cursor, parent=None):
		SqlTableModel.__init__(self, parent)
		try:
			resdata = cursor.fetchall()
			if cursor.description != None:
				self.header = map(lambda x: x[0], cursor.description)
				self.resdata = resdata
		except sqlite.OperationalError, e:
			pass # nothing to fetch!

