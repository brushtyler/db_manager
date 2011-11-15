# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name                 : DB Manager
Description          : Database manager plugin for QuantumGIS
Date                 : May 23, 2011
copyright            : (C) 2011 by Giuseppe Sucameli
email                : brush.tyler@gmail.com

The content of this file is based on 
- PG_Manager by Martin Dobias <wonder.sk@gmail.com> (GPLv2 license)
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

import psycopg2

def classFactory():
	return PostGisDBConnector

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
			self.connection = psycopg2.connect( self._connectionInfo().encode('utf-8') )
		except psycopg2.OperationalError, e:
			raise ConnectionError( e.args[0] )
		
		self._checkSpatial()
		self._checkRaster()
		self._checkGeometryColumnsTable()
		self._checkRasterColumnsTable()

	def _connectionInfo(self):
		return unicode(self._uri.connectionInfo())

	def _checkSpatial(self):
		""" check whether postgis_version is present in catalog """
		c = self.connection.cursor()
		self._execute(c, u"SELECT COUNT(*) FROM pg_proc WHERE proname = 'postgis_version'")
		self.has_spatial = c.fetchone()[0] > 0
		return self.has_spatial
	
	def _checkRaster(self):
		""" check whether postgis_version is present in catalog """
		c = self.connection.cursor()
		self._execute(c, u"SELECT COUNT(*) FROM pg_proc WHERE proname = 'postgis_raster_lib_version'")
		self.has_raster = c.fetchone()[0] > 0
		return self.has_raster
	
	def _checkGeometryColumnsTable(self):
		c = self.connection.cursor()
		self._execute(c, u"SELECT relkind = 'v' FROM pg_class WHERE relname = 'geometry_columns' AND relkind IN ('v', 'r')")
		res = c.fetchone()
		self.has_geometry_columns = (res != None and len(res) != 0)
		
		if not self.has_geometry_columns:
			self.has_geometry_columns_access = self.is_geometry_columns_view = False
		else:
			self.is_geometry_columns_view = res[0]
			# find out whether has privileges to access geometry_columns table
			priv = self.getTablePrivileges('geometry_columns')
			self.has_geometry_columns_access = priv[0]
		return self.has_geometry_columns

	def _checkRasterColumnsTable(self):
		c = self.connection.cursor()
		self._execute(c, u"SELECT relkind = 'v' FROM pg_class WHERE relname = 'raster_columns' AND relkind IN ('v', 'r')")
		res = c.fetchone()
		self.has_raster_columns = (res != None and len(res) != 0)
		
		if not self.has_raster_columns:
			self.has_raster_columns_access = self.is_raster_columns_view = False
		else:
			self.is_raster_columns_view = res[0]
			# find out whether has privileges to access geometry_columns table
			self.has_raster_columns_access = self.getTablePrivileges('raster_columns')[0]
		return self.has_raster_columns

	def getInfo(self):
		c = self.connection.cursor()
		self._execute(c, u"SELECT version()")
		return c.fetchone()

	def getSpatialInfo(self):
		""" returns tuple about postgis support:
			- lib version
			- installed scripts version
			- released scripts version
			- geos version
			- proj version
			- whether uses stats
		"""
		if not self.has_spatial:
			return

		c = self.connection.cursor()
		try:
			self._execute(c, u"SELECT postgis_lib_version(), postgis_scripts_installed(), postgis_scripts_released(), postgis_geos_version(), postgis_proj_version(), postgis_uses_stats()")
		except DbError:
			return

		return c.fetchone()


	def getDatabasePrivileges(self):
		""" db privileges: (can create schemas, can create temp. tables) """
		sql = u"SELECT has_database_privilege(%(d)s, 'CREATE'), has_database_privilege(%(d)s, 'TEMP')" % { 'd' : self.quoteString(self.dbname) }
		c = self.connection.cursor()
		self._execute(c, sql)
		return c.fetchone()
		
	def getSchemaPrivileges(self, schema):
		""" schema privileges: (can create new objects, can access objects in schema) """
		schema = 'current_schema()' if schema == None else self.quoteString(schema)
		sql = u"SELECT has_schema_privilege(%(s)s, 'CREATE'), has_schema_privilege(%(s)s, 'USAGE')" % { 's' : schema }
		c = self.connection.cursor()
		self._execute(c, sql)
		return c.fetchone()
	
	def getTablePrivileges(self, table, schema=None):
		""" table privileges: (select, insert, update, delete) """
		schema_priv = self.getSchemaPrivileges(schema)
		if not schema_priv[1]:
			return
		t = self.quoteId( (schema,table) )
		sql = u"""SELECT has_table_privilege(%(t)s, 'SELECT'), has_table_privilege(%(t)s, 'INSERT'),
		                has_table_privilege(%(t)s, 'UPDATE'), has_table_privilege(%(t)s, 'DELETE')""" % { 't': self.quoteString(t) }
		c = self.connection.cursor()
		self._execute(c, sql)
		return c.fetchone()


	def getSchemas(self):
		""" get list of schemas in tuples: (oid, name, owner, perms) """
		c = self.connection.cursor()
		sql = u"SELECT oid, nspname, pg_get_userbyid(nspowner), nspacl, pg_catalog.obj_description(oid) FROM pg_namespace WHERE nspname !~ '^pg_' AND nspname != 'information_schema' ORDER BY nspname"
		self._execute(c, sql)
		return c.fetchall()

	def getTables(self, schema=None):
		""" get list of tables """
		tablenames = []
		items = []

		sys_tables = [ "spatial_ref_sys", "geography_columns", "geometry_columns", 
				"raster_columns", "raster_overviews" ]

		vectors = self.getVectorTables(schema)
		for tbl in vectors:
			if tbl[1] in sys_tables and tbl[2] in ['', 'public']:
				continue
			tablenames.append( (tbl[2], tbl[1]) )
			items.append( tbl )

		rasters = self.getRasterTables(schema)
		for tbl in rasters:
			if tbl[1] in sys_tables and tbl[2] in ['', 'public']:
				continue
			tablenames.append( (tbl[2], tbl[1]) )
			items.append( tbl )


		c = self.connection.cursor()

		sys_tables = [ "spatial_ref_sys", "geography_columns", "geometry_columns", 
				"raster_columns", "raster_overviews" ]
		
		if schema:
			schema_where = u" AND nspname = %s " % self.quoteString(schema)
		else:
			schema_where = u" AND (nspname != 'information_schema' AND nspname !~ 'pg_') "
			
		# get all tables and views
		sql = u"""SELECT 
						cla.relname, nsp.nspname, cla.relkind = 'v', 
						pg_get_userbyid(relowner), reltuples, relpages, 
						pg_catalog.obj_description(cla.oid)
					FROM pg_class AS cla 
					JOIN pg_namespace AS nsp ON nsp.oid = cla.relnamespace
					WHERE cla.relkind IN ('v', 'r') """ + schema_where + """
					ORDER BY nsp.nspname, cla.relname"""
						  
		self._execute(c, sql)

		for tbl in c.fetchall():
			if tablenames.count( (tbl[1], tbl[0]) ) <= 0:
				item = list(tbl)
				item.insert(0, Table.TableType)
				items.append( item )

		return sorted( items, cmp=lambda x,y: cmp((x[2],x[1]), (y[2],y[1])) )


	def getVectorTables(self, schema=None):
		""" get list of table with a geometry column
			it returns:
				name (table name)
				namespace (schema)
				type = 'view' (is a view?)
				owner 
				tuples
				pages
				geometry_column:
					f_geometry_column (or pg_attribute.attname, the geometry column name)
					type (or pg_attribute.atttypid::regtype, the geometry column type name)
					coord_dimension 
					srid
		"""

		if not self.has_spatial:
			return []

		c = self.connection.cursor()
		
		if schema:
			schema_where = u" AND nspname = %s " % self.quoteString(schema)
		else:
			schema_where = u" AND (nspname != 'information_schema' AND nspname !~ 'pg_') "

		geometry_column_from = u""
		geometry_fields_select = u"""att.attname, 
						textin(regtypeout(att.atttypid::regtype)), 
						NULL, NULL"""
		if self.has_geometry_columns and self.has_geometry_columns_access:
			geometry_column_from = u"""LEFT OUTER JOIN geometry_columns AS geo ON 
						cla.relname = geo.f_table_name AND nsp.nspname = f_table_schema AND 
						lower(att.attname) = lower(f_geometry_column)"""
			geometry_fields_select = u"""CASE WHEN geo.f_geometry_column IS NOT NULL THEN geo.f_geometry_column ELSE att.attname END, 
						CASE WHEN geo.type IS NOT NULL THEN geo.type ELSE textin(regtypeout(att.atttypid::regtype)) END, 
						geo.coord_dimension, geo.srid"""
			

		# discovery of all tables and whether they contain a geometry column
		sql = u"""SELECT 
						cla.relname, nsp.nspname, cla.relkind = 'v', 
						pg_get_userbyid(relowner), cla.reltuples, cla.relpages, 
						pg_catalog.obj_description(cla.oid), 
						""" + geometry_fields_select + """

					FROM pg_class AS cla 
					JOIN pg_namespace AS nsp ON 
						nsp.oid = cla.relnamespace

					JOIN pg_attribute AS att ON 
						att.attrelid = cla.oid AND 
						att.atttypid = 'geometry'::regtype OR 
						att.atttypid IN (SELECT oid FROM pg_type WHERE typbasetype='geometry'::regtype ) 

					""" + geometry_column_from + """ 

					WHERE cla.relkind IN ('v', 'r') """ + schema_where + """ 
					ORDER BY nsp.nspname, cla.relname, att.attname"""

		self._execute(c, sql)

		items = []
		for i, tbl in enumerate(c.fetchall()):
			item = list(tbl)
			item.insert(0, Table.VectorType)
			items.append( item )
			
		return items

	def getRasterTables(self, schema=None):
		""" get list of table with a raster column
			it returns:
				name (table name)
				namespace (schema)
				type = 'view' (is a view?)
				owner 
				tuples
				pages
				raster_column:
					r_column (or pg_attribute.attname, the raster column name)
					pixel type
					block size
					internal or external
					srid
		"""

		if not self.has_spatial:
			return []
		if not self.has_raster:
			return []

		c = self.connection.cursor()
		
		if schema:
			schema_where = u" AND nspname = %s " % self.quoteString(schema)
		else:
			schema_where = u" AND (nspname != 'information_schema' AND nspname !~ 'pg_') "

		raster_column_from = u""
		raster_fields_select = u"""att.attname, NULL, NULL, NULL, NULL, NULL"""
		if self.has_raster_columns and self.has_raster_columns_access:
			raster_column_from = u"""LEFT OUTER JOIN raster_columns AS geo ON 
						cla.relname = geo.r_table_name AND nsp.nspname = r_table_schema AND 
						lower(att.attname) = lower(r_column)"""
			raster_fields_select = u"""CASE WHEN geo.r_column IS NOT NULL THEN geo.r_column ELSE att.attname END, 
						geo.pixel_types,
						geo.scale_x,
						geo.scale_y,
						geo.out_db,
						geo.srid"""


		# discovery of all tables and whether they contain a geometry column
		sql = u"""SELECT 
						cla.relname, nsp.nspname, cla.relkind = 'v', 
						pg_get_userbyid(relowner), cla.reltuples, cla.relpages, 
						pg_catalog.obj_description(cla.oid), 
						""" + raster_fields_select + """

					FROM pg_class AS cla 
					JOIN pg_namespace AS nsp ON 
						nsp.oid = cla.relnamespace

					JOIN pg_attribute AS att ON 
						att.attrelid = cla.oid AND 
						att.atttypid = 'raster'::regtype OR 
						att.atttypid IN (SELECT oid FROM pg_type WHERE typbasetype='raster'::regtype ) 

					""" + raster_column_from + """ 

					WHERE cla.relkind IN ('v', 'r') """ + schema_where + """ 
					ORDER BY nsp.nspname, cla.relname, att.attname"""

		self._execute(c, sql)

		items = []
		for i, tbl in enumerate(c.fetchall()):
			item = list(tbl)
			item.insert(0, Table.RasterType)
			items.append( item )
			
		return items


	def getTableRowCount(self, table, schema=None):
		c = self.connection.cursor()
		self._execute( c, u"SELECT COUNT(*) FROM %s" % self.quoteId( (schema, table) ) )
		return c.fetchone()[0]

	def getTableFields(self, table, schema=None):
		""" return list of columns in table """
		c = self.connection.cursor()
		schema_where = u" AND nspname=%s " % self.quoteString(schema) if schema is not None else ""
		sql = u"""SELECT a.attnum AS ordinal_position,
				a.attname AS column_name,
				t.typname AS data_type,
				a.attlen AS char_max_len,
				a.atttypmod AS modifier,
				a.attnotnull AS notnull,
				a.atthasdef AS hasdefault,
				adef.adsrc AS default_value, 
				pg_catalog.format_type(a.atttypid,a.atttypmod) AS formatted_type
			FROM pg_class c
			JOIN pg_attribute a ON a.attrelid = c.oid
			JOIN pg_type t ON a.atttypid = t.oid
			JOIN pg_namespace nsp ON c.relnamespace = nsp.oid
			LEFT JOIN pg_attrdef adef ON adef.adrelid = a.attrelid AND adef.adnum = a.attnum
			WHERE
			  a.attnum > 0 AND c.relname=%s %s
			ORDER BY a.attnum""" % (self.quoteString(table), schema_where)

		self._execute(c, sql)
		return c.fetchall()

	def getTableIndexes(self, table, schema=None):
		""" get info about table's indexes. ignore primary key constraint index, they get listed in constaints """
		schema_where = u" AND nspname=%s " % self.quoteString(schema) if schema is not None else ""
		sql = u"""SELECT relname, indkey, indisunique = 't' 
						FROM pg_index JOIN pg_class ON pg_index.indrelid=pg_class.oid 
						JOIN pg_namespace nsp ON pg_class.relnamespace = nsp.oid 
							WHERE pg_class.relname=%s %s 
							AND indisprimary != 't' """ % (self.quoteString(table), schema_where)
		c = self.connection.cursor()
		self._execute(c, sql)
		return c.fetchall()
	
	
	def getTableConstraints(self, table, schema=None):
		c = self.connection.cursor()
		
		schema_where = u" AND nspname=%s " % self.quoteString(schema) if schema is not None else ""
		sql = u"""SELECT c.conname, c.contype, c.condeferrable, c.condeferred, array_to_string(c.conkey, ' '), c.consrc,
		         t2.relname, c.confupdtype, c.confdeltype, c.confmatchtype, array_to_string(c.confkey, ' ') FROM pg_constraint c
		  LEFT JOIN pg_class t ON c.conrelid = t.oid
			LEFT JOIN pg_class t2 ON c.confrelid = t2.oid
			JOIN pg_namespace nsp ON t.relnamespace = nsp.oid
			WHERE t.relname = %s %s """ % (self.quoteString(table), schema_where)
		
		self._execute(c, sql)
		return c.fetchall()


	def getTableTriggers(self, table, schema=None):
		c = self.connection.cursor()
		
		schema_where = u" AND nspname=%s " % self.quoteString(schema) if schema is not None else ""
		sql = u"""SELECT tgname, proname, tgtype, tgenabled FROM pg_trigger trig
		          LEFT JOIN pg_class t ON trig.tgrelid = t.oid
							LEFT JOIN pg_proc p ON trig.tgfoid = p.oid
							JOIN pg_namespace nsp ON t.relnamespace = nsp.oid
							WHERE t.relname = %s %s """ % (self.quoteString(table), schema_where)
	
		self._execute(c, sql)
		return c.fetchall()

	def enableAllTableTriggers(self, enable, table, schema=None):
		""" enable or disable all triggers on table """
		self.enableTableTrigger(None, enable, table, schema)
		
	def enableTableTrigger(self, trigger, enable, table, schema=None):
		""" enable or disable one trigger on table """
		trigger = self.quoteId(trigger) if trigger != None else "ALL"
		sql = u"ALTER TABLE %s %s TRIGGER %s" % (self.quoteId( (schema, table) ), "ENABLE" if enable else "DISABLE", trigger)
		self._execute_and_commit(sql)
		
	def deleteTableTrigger(self, trigger, table, schema=None):
		""" delete trigger on table """
		sql = u"DROP TRIGGER %s ON %s" % (self.quoteId(trigger), self.quoteId( (schema, table) ))
		self._execute_and_commit(sql)
		
	
	def getTableRules(self, table, schema=None):
		c = self.connection.cursor()
		
		schema_where = u" AND schemaname=%s " % self.quoteString(schema) if schema is not None else ""
		sql = u"""SELECT rulename, definition FROM pg_rules
					WHERE tablename=%s %s """ % (self.quoteString(table), schema_where)
	
		self._execute(c, sql)
		return c.fetchall()

	def deleteTableRule(self, rule, table, schema=None):
		""" delete rule on table """
		sql = u"DROP RULE %s ON %s" % (self.quoteId(rule), self.quoteId( (schema, table) ))
		self._execute_and_commit(sql)


	def getTableEstimatedExtent(self, geom, table, schema=None):
		""" find out estimated extent (from the statistics) """
		c = self.connection.cursor()

		schema_part = u"%s, " % self.quoteString(schema) if schema is not None else ""
		if self.isRasterTable(table, schema):
			extent = u"estimated_extent(%s,%s,st_convexhull(%s))" % (schema_part, self.quoteString(table), self.quoteString(geom))
		else:
			extent = u"estimated_extent(%s,%s,%s)" % (schema_part, self.quoteString(table), self.quoteString(geom))
		sql = u"""SELECT xmin(%(ext)s), ymin(%(ext)s), xmax(%(ext)s), ymax(%(ext)s) """ % { 'ext' : extent }
		try:
			self._execute(c, sql)
		except DbError, e:
			return
		return c.fetchone()
	
	def getViewDefinition(self, view, schema=None):
		""" returns definition of the view """
		schema_where = u" AND nspname=%s " % self.quoteString(schema) if schema is not None else ""
		sql = u"""SELECT pg_get_viewdef(c.oid) FROM pg_class c
						JOIN pg_namespace nsp ON c.relnamespace = nsp.oid
		        WHERE relname=%s %s AND relkind='v' """ % (self.quoteString(view), schema_where)
		c = self.connection.cursor()
		self._execute(c, sql)
		return c.fetchone()[0]

	def getSpatialRefInfo(self, srid):
		if not self.has_spatial:
			return
		
		try:
			c = self.connection.cursor()
			self._execute(c, "SELECT srtext FROM spatial_ref_sys WHERE srid = '%d'" % srid)
			sr = c.fetchone()
			if sr == None:
				return
			srtext = sr[0]
			# try to extract just SR name (should be quoted in double quotes)
			regex = QRegExp( '"([^"]+)"' )
			if regex.indexIn( srtext ) > -1:
				srtext = regex.cap(1)
			return srtext
		except DbError, e:
			return


	def createTable(self, table, fields, schema=None):
		""" create ordinary table
				'fields' is array containing instances of TableField
				'pkey' contains name of column to be used as primary key
		"""
		if len(fields) == 0:
			return False

		fields_def = map(lambda x: x.definition(), fields)
		pkeys = filter(lambda x: x.primaryKey, fields)

		sql = "CREATE TABLE %s (" % self.quoteId( (schema, table) )
		sql += u", ".join( fields_def )
		if len(pkeys) > 0:
			sql += u", PRIMARY KEY (%s)" % self.quoteId(pkeys[0].name)
		sql += ")"

		self._execute_and_commit(sql)
		return True

	def addGeometryColumn(self, table, geom_type, schema=None, geom_column='the_geom', srid=-1, dim=2):
		# use schema if explicitly specified
		schema_part = u""
		if schema:
			schema_part = u"%s, " % self.quoteString(schema)
		sql = u"SELECT AddGeometryColumn(%s%s, %s, %d, %s, %d)" % (schema_part, self.quoteString(table), self.quoteString(geom_column), srid, self.quoteString(geom_type), dim)
		self._execute_and_commit(sql)

	def createSpatialIndex(self, table, schema=None, geom_column='the_geom'):
		idx_name = self.quoteId("sidx_%s" % table)
		sql = u"CREATE INDEX %s ON %s USING GIST(%s)" % (idx_name, self.quoteId((schema, table)), self.quoteId(geom_column))
		self._execute_and_commit(sql)


	def isVectorTable(self, table, schema=None):
		if self.has_geometry_columns and self.has_geometry_columns_access:
			c = self.connection.cursor()
			sql = u"SELECT count(*) FROM geometry_columns WHERE f_table_schema = %s AND f_table_name = %s" % (self.quoteString(schema), self.quoteString(table))
			self._execute(c, sql)
			return c.fetchone()[0] > 0
		return False

	def isRasterTable(self, table, schema=None):
		if self.has_raster_columns and self.has_raster_columns_access:
			c = self.connection.cursor()
			sql = u"SELECT count(*) FROM raster_columns WHERE r_table_schema = %s AND r_table_name = %s" % (self.quoteString(schema), self.quoteString(table))
			self._execute(c, sql)
			return c.fetchone()[0] > 0
		return False		


	def deleteTable(self, table, schema=None):
		""" delete table and its reference in either geometry_columns or raster_columns """
		schema_part = u"%s, " % self.quoteString(schema) if schema is not None else ""
		if self.isVectorTable(table, schema):
			sql = u"SELECT DropGeometryTable(%s%s)" % (schema_part, self.quoteString(table))
		elif self.isRasterTable(table, schema):
			sql = u"SELECT DropRasterTable(%s%s)" % (schema_part, self.quoteString(table))
		else:
			sql = u"DROP TABLE %s" % self.quoteId( (schema, table) )
		self._execute_and_commit(sql)


	def emptyTable(self, table, schema=None):
		""" delete all rows from table """
		sql = u"TRUNCATE %s" % self.quoteId( (schema, table) )
		self._execute_and_commit(sql)

	def renameTable(self, table, new_table, schema=None):
		""" rename a table in database """
		if new_table == table:
			return
		c = self.connection.cursor()

		sql = u"ALTER TABLE %s RENAME TO %s" % (self.quoteId( (schema, table) ), self.quoteId(new_table))
		self._execute(c, sql)
		
		# update geometry_columns if postgis is enabled
		if self.has_geometry_columns and not self.is_geometry_columns_view:
			schema_where = u" AND f_table_schema=%s " % self.quoteString(schema) if schema is not None else ""
			sql = u"UPDATE geometry_columns SET f_table_name=%s WHERE f_table_name=%s %s" % (self.quoteString(new_table), self.quoteString(table), schema_where)
			self._execute(c, sql)

		self.connection.commit()

	def moveTableToSchema(self, table, new_schema, schema=None):
		if new_schema == schema:
			return
		c = self.connection.cursor()

		sql = u"ALTER TABLE %s SET SCHEMA %s" % (self.quoteId( (schema, table) ), self.quoteId(new_schema))
		self._execute(c, sql)
		
		# update geometry_columns if postgis is enabled
		if self.has_geometry_columns and not self.is_geometry_columns_view:
			schema_where = u" AND f_table_schema=%s " % self.quoteString(schema) if schema is not None else ""
			sql = u"UPDATE geometry_columns SET f_table_schema=%s WHERE f_table_name=%s %s" % (self.quoteString(new_schema), self.quoteString(table), schema_where)
			self._execute(c, sql)

		self.connection.commit()

	def moveTable(self, table, new_table, schema=None, new_schema=None):
		if new_schema == schema and new_table == table: 
			return
		if new_schema == schema:
			return self.renameTable(table, new_table, schema)
		if new_table == table:
			return self.moveTableToSchema(table, new_schema, schema)

		c = self.connection.cursor()
		t = u"__new_table__"

		sql = u"ALTER TABLE %s RENAME TO %s" % (self.quoteId( (schema, table) ), self.quoteId(t))
		self._execute(c, sql)

		sql = u"ALTER TABLE %s SET SCHEMA %s" % (self.quoteId( (schema, t) ), self.quoteId(new_schema))
		self._execute(c, sql)

		sql = u"ALTER TABLE %s RENAME TO %s" % (self.quoteId( (new_schema, t) ), self.quoteId(table))
		self._execute(c, sql)

		# update geometry_columns if postgis is enabled
		if self.has_geometry_columns and not self.is_geometry_columns_view:
			schema_where = u" f_table_schema=%s AND " % self.quoteString(schema) if schema is not None else ""
			schema_part = u" f_table_schema=%s, " % self.quoteString(schema) if schema is not None else ""
			sql = u"UPDATE geometry_columns SET %s f_table_name=%s WHERE %s f_table_name=%s" % (schema_part, self.quoteString(new_schema), self.quoteString(new_table), schema_where, self.quoteString(table))
			self._execute(c, sql)

		self.connection.commit()
		
	def createView(self, name, query, schema=None):
		sql = u"CREATE VIEW %s AS %s" % (self.quoteId( (schema, table) ), query)
		self._execute_and_commit(sql)
	
	def deleteView(self, name, schema=None):
		sql = u"DROP VIEW %s" % self.quoteId( (schema, name) )
		self._execute_and_commit(sql)
	
	def renameView(self, name, new_name, schema=None):
		""" rename view in database """
		self.renameTable(name, new_name, schema)
		
	def createSchema(self, schema):
		""" create a new empty schema in database """
		sql = u"CREATE SCHEMA %s" % self.quoteId(schema)
		self._execute_and_commit(sql)
		
	def deleteSchema(self, schema):
		""" drop (empty) schema from database """
		sql = u"DROP SCHEMA %s" % self.quoteId(schema)
		self._execute_and_commit(sql)
		
	def renameSchema(self, schema, new_schema):
		""" rename a schema in database """
		sql = u"ALTER SCHEMA %s RENAME TO %s" % (self.quoteId(schema), self.quoteId(new_schema))
		self._execute_and_commit(sql)


	def hasCustomQuerySupport(self):
		from qgis.core import QGis
		return QGis.QGIS_VERSION[0:3] >= "1.5"

	def runVacuumAnalyze(self, table, schema=None):
		""" run vacuum analyze on a table """
		# vacuum analyze must be run outside transaction block - we have to change isolation level
		self.connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
		c = self.connection.cursor()
		sql = u"VACUUM ANALYZE %s" % self.quoteId( (schema, table) )
		self._execute(c, sql)
		self.connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED)


	def fieldTypes(self):
		return [
			"integer", "bigint", "smallint", # integers
			"serial", "bigserial", # auto-incrementing ints
			"real", "double precision", "numeric", # floats
			"varchar", "varchar(n)", "char(n)", "text", # strings
			"date", "time", "timestamp" # date/time
		]

		
	def _execute(self, cursor, sql):
		try:
			cursor.execute(unicode(sql))
		except psycopg2.Error, e:
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
		except psycopg2.Error, e:
			# do the rollback to avoid a "current transaction aborted, commands ignored" errors
			self.connection.rollback()
			raise DbError(e)

	def _fetchone(self, c):
		try:
			return c.fetchone()
		except psycopg2.Error, e:
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

