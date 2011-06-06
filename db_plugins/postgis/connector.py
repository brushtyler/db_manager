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
import psycopg2

class PostGisDBConnector(DBConnector):
	def __init__(self, uri):
		DBConnector.__init__(self, uri)

		self.host = uri.host()
		self.port = uri.port()
		self.dbname = uri.database()
		self.user = uri.username()
		self.passwd = uri.password()
				
		if self.dbname == '' or self.dbname is None:
			self.dbname = self.user
		
		try:
			self.con = psycopg2.connect( self.__connectionInfo() )
		except psycopg2.OperationalError, e:
			raise DbError(e)
		
		self.has_spatial = self.__checkSpatial()
		self.__checkGeometryColumnsTable()

		# a counter to ensure that the cursor will be unique
		self.last_cursor_id = 0

	def __connectionInfo(self):
		conn_str = u''
		if self.host:   conn_str += "host='%s' "     % self.host
		if self.port:   conn_str += "port=%s "       % self.port
		if self.dbname: conn_str += "dbname='%s' "   % self.dbname
		if self.user:   conn_str += "user='%s' "     % self.user
		if self.passwd: conn_str += "password='%s' " % self.passwd
		return conn_str


	def __checkSpatial(self):
		""" check whether postgis_version is present in catalog """
		c = self.con.cursor()
		self._exec_sql(c, "SELECT COUNT(*) FROM pg_proc WHERE proname = 'postgis_version'")
		return (c.fetchone()[0] > 0)
	
	def __checkGeometryColumnsTable(self):
		c = self.con.cursor()
		self._exec_sql(c, "SELECT relname FROM pg_class WHERE relname = 'geometry_columns' AND pg_class.relkind IN ('v', 'r')")
		self.has_geometry_columns = (len(c.fetchall()) != 0)
		
		if not self.has_geometry_columns:
			self.has_geometry_columns_access = False
			return
			
		# find out whether has privileges to access geometry_columns table
		self.has_geometry_columns_access = self.getTablePrivileges('geometry_columns')[0]

	def getInfo(self):
		return ""

	def getSpatialInfo(self):
		""" returns tuple about postgis support:
			- lib version
			- installed scripts version
			- released scripts version
			- geos version
			- proj version
			- whether uses stats
		"""
		c = self.con.cursor()
		self._exec_sql(c, "SELECT postgis_lib_version(), postgis_scripts_installed(), postgis_scripts_released(), postgis_geos_version(), postgis_proj_version(), postgis_uses_stats()")
		return c.fetchone()


	def getDatabasePrivileges(self):
		""" db privileges: (can create schemas, can create temp. tables) """
		sql = "SELECT has_database_privilege('%(d)s', 'CREATE'), has_database_privilege('%(d)s', 'TEMP')" % { 'd' : self.quoteString(self.dbname) }
		c = self.con.cursor()
		self._exec_sql(c, sql)
		return c.fetchone()
		
	def getSchemaPrivileges(self, schema):
		""" schema privileges: (can create new objects, can access objects in schema) """
		sql = "SELECT has_schema_privilege('%(s)s', 'CREATE'), has_schema_privilege('%(s)s', 'USAGE')" % { 's' : self.quoteString(schema) }
		c = self.con.cursor()
		self._exec_sql(c, sql)
		return c.fetchone()
	
	def getTablePrivileges(self, table, schema=None):
		""" table privileges: (select, insert, update, delete) """
		t = self.quoteId( (schema,table) )
		sql = """SELECT has_table_privilege('%(t)s', 'SELECT'), has_table_privilege('%(t)s', 'INSERT'),
		                has_table_privilege('%(t)s', 'UPDATE'), has_table_privilege('%(t)s', 'DELETE')""" % { 't': self.quoteString(t) }
		c = self.con.cursor()
		self._exec_sql(c, sql)
		return c.fetchone()


	def schemas(self):
		""" get list of schemas in tuples: (oid, name, owner, perms) """
		c = self.con.cursor()
		sql = "SELECT oid, nspname, pg_get_userbyid(nspowner), nspacl FROM pg_namespace WHERE nspname !~ '^pg_' AND nspname != 'information_schema'"
		self._exec_sql(c, sql)

		schema_cmp = lambda x,y: cmp(unicode(x[1]).lower(), unicode(y[1]).lower())
		return map(lambda x: Schema(x), sorted(c.fetchall(), cmp=schema_cmp))

	def tables(self, schema=None):
		"""
			get list of tables with schemas, whether user has privileges, whether table has geometry column(s) etc.
			
			geometry_columns:
			- f_table_schema
			- f_table_name
			- f_geometry_column
			- coord_dimension
			- srid
			- type
		"""
		c = self.con.cursor()
		
		if schema:
			schema_where = " AND nspname = '%s' " % self.quoteString(schema)
		else:
			schema_where = " AND (nspname != 'information_schema' AND nspname !~ 'pg_') "
			
		# LEFT OUTER JOIN: like LEFT JOIN but if there are more matches, for join, all are used (not only one)
		
		# first find out whether postgis is enabled
		if not self.has_spatial:
			# get all tables and views
			sql = """SELECT pg_class.relname, pg_namespace.nspname, pg_class.relkind = 'v', pg_get_userbyid(relowner), reltuples, relpages, NULL, NULL, NULL, NULL
							FROM pg_class
							JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace
							WHERE pg_class.relkind IN ('v', 'r')""" + schema_where + "ORDER BY nspname, relname"
		else:
			# discovery of all tables and whether they contain a geometry column
			sql = """SELECT pg_class.relname, pg_namespace.nspname, pg_class.relkind, pg_get_userbyid(relowner), reltuples, relpages, pg_attribute.attname, pg_attribute.atttypid::regtype, NULL, NULL
							FROM pg_class
							JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace
							LEFT OUTER JOIN pg_attribute ON pg_attribute.attrelid = pg_class.oid AND
									( pg_attribute.atttypid = 'geometry'::regtype
										OR pg_attribute.atttypid IN (SELECT oid FROM pg_type WHERE typbasetype='geometry'::regtype ) )
							WHERE pg_class.relkind IN ('v', 'r')""" + schema_where + "ORDER BY nspname, relname, attname"
						  
		self._exec_sql(c, sql)
		items = c.fetchall()
		
		# get geometry info from geometry_columns if exists
		if self.has_spatial and self.has_geometry_columns and self.has_geometry_columns_access:
			sql = """SELECT relname, nspname, relkind, pg_get_userbyid(relowner), reltuples, relpages,
							geometry_columns.f_geometry_column, geometry_columns.type, geometry_columns.coord_dimension, geometry_columns.srid
							FROM pg_class
						  JOIN pg_namespace ON relnamespace=pg_namespace.oid
						  LEFT OUTER JOIN geometry_columns ON relname=f_table_name AND nspname=f_table_schema
						  WHERE (relkind = 'r' or relkind='v') """ + schema_where + "ORDER BY nspname, relname, f_geometry_column"
			self._exec_sql(c, sql)
			
			# merge geometry info to "items"
			for i, geo_item in enumerate(c.fetchall()):
				if geo_item[7]:
					items[i] = geo_item
			
		return map(lambda x: Table(x), items)

		
	def _exec_sql(self, cursor, sql):
		try:
			cursor.execute(sql)
		except psycopg2.Error, e:
			# do the rollback to avoid a "current transaction aborted, commands ignored" errors
			self.con.rollback()
			raise DbError(e)
		
	def _exec_sql_and_commit(self, sql):
		""" tries to execute and commit some action, on error it rolls back the change """
		c = self.con.cursor()
		self._exec_sql(c, sql)
		self.con.commit()


class Schema:
	def __init__(self, row):
		self.oid, self.name, self.owner, self.perms = row

class Table:
	def __init__(self, row):
		self.name, self.schema, self.isView, self.owner, self.tuples, self.pages, self.geomCol, self.geomType, self.geomDim, self.srid = row

