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
	return PostGisDBPlugin

class PostGisDBPlugin(DBPlugin):

	@classmethod
	def icon(self):
		return QIcon(":/icons/postgis_elephant.png")

	@classmethod
	def typeName(self):
		return 'postgis'

	@classmethod
	def typeNameString(self):
		return 'PostGIS'

	@classmethod
	def connectionSettingsKey(self):
		return '/PostgreSQL/connections'

	def connect(self, parent=None):
		conn_name = self.connectionName()
		settings = QSettings()
		settings.beginGroup( u"/%s/%s" % (self.connectionSettingsKey(), conn_name) )

		if not settings.contains( "database" ): # non-existent entry?
			raise InvalidDataException( 'there is no defined database connection "%s".' % conn_name )
	
		get_value_str = lambda x: unicode(settings.value(x).toString())
		host, port, database, username, password = map(get_value_str, ["host", "port", "database", "username", "password"])

		# qgis1.5 use 'savePassword' instead of 'save' setting
		if not ( settings.value("save").toBool() or settings.value("savePassword").toBool() ):
			#dlg = qgis.gui.QgsCredentialDialog(parent)
			#(ok, username, password) = dlg.request(selected)
			(password, ok) = QInputDialog.getText(parent, "Enter password", 'Enter password for connection "%s":' % conn_name, QLineEdit.Password)
			if not ok: return False

		settings.endGroup()

		import qgis.core
		from .connector import PostGisDBConnector
		uri = qgis.core.QgsDataSourceURI()
		uri.setConnection(host, port, database, username, password)
		self.db = PGDatabase( self, PostGisDBConnector(uri) )
		return True


class PGDatabase(Database):
	def __init__(self, connection, connector):
		Database.__init__(self, connection, connector)

	def generalInfo(self):
		info = self.connector.getInfo()
		return [
			("Server version: ", info[0])
		]

	def connectionDetails(self):
		return [ 
			("Host:", self.connector.host), 
			("User:", self.connector.user)
		]

	def spatialInfo(self):
		info = self.connector.getSpatialInfo()
		ret = [
			("Library:", info[0]), 
			("Scripts:", info[1]),
			("GEOS:", info[3]), 
			("Proj:", info[4]), 
			("Use stats:", info[5]) 
		]

		if info[1] != None and info[1] != info[2]:
			ret.append( u"\n<warning> Version of installed scripts doesn't match version of released scripts!\n" \
				"This is probably a result of incorrect PostGIS upgrade." )

		if not self.connector.has_geometry_columns:
			ret.append( u"\n<warning> geometry_columns table doesn't exist!\n" \
				"This table is essential for many GIS applications for enumeration of tables." )
		elif not self.connector.has_geometry_columns_access:
			ret.append( u"\n<warning> This user doesn't have privileges to read contents of geometry_columns table!\n" \
				"This table is essential for many GIS applications for enumeration of tables." )

		return ret

	def privilegesDetails(self):
		details = self.connector.getDatabasePrivileges()
		ret = []
		if details[0]: ret.append("create new schemas") 
		if details[1]: ret.append("create temporary tables") 
		return ret


	def schemas(self):
		return map(lambda x: PGSchema(x, self), self.connector.getSchemas())

	def tables(self, schema=None):
		return map(lambda x: PGTable(x, self, schema), self.connector.getTables(schema.name))


class PGSchema(Schema):
	def __init__(self, row, db):
		Schema.__init__(self, db)
		self.oid, self.name, self.owner, self.perms = row
		self.tableCount = len(self.tables())

	def generalInfo(self):
		info = [
			("Tables:", self.tableCount)
		]
		if self.owner: info.append( ("Owner", self.owner) )
		return info

	def privilegesDetails(self):
		details = self._db.connector.getSchemaPrivileges(self.name)
		ret = []
		if details[0]: ret.append("create new objects")
		if details[1]: ret.append("access objects")
		return ret

class PGTable(Table):
	def __init__(self, row, db, schema=None):
		Table.__init__(self, db, schema)
		self.name, schema_name, self.isView, self.owner, self.estimatedRowCount, self.pages, self.geomColumn, self.geomType, self.geomDim, self.srid = row
		self.estimatedRowCount = int(self.estimatedRowCount)
		self._constraints = self._rules = None

	def generalInfo(self):
		# if the estimation is less than 100 rows, try to count them - it shouldn't take long time
		if self.rowCount == None and self.estimatedRowCount < 100:
			self.runAction("rows/count")

		ret = [
			("Relation type:", "View" if self.isView else "Table"), 
			("Owner:", self.owner), 
			("Pages:", self.pages), 
			("Rows (estimation):", self.estimatedRowCount )
		]

		if self.rowCount == None or (isinstance(self.rowCount, int) and self.rowCount >= 0):
			ret.append( ("Rows (counted):", self.rowCount if self.rowCount != None else 'Unknown (<a href="action:rows/count">find out</a>)') )

		# privileges
		schema_priv = self._schema.privilegesDetails() if self._schema else None
		# has the user access to this schema?
		if schema_priv == None:
			pass
		elif len(schema_priv) <= 0:
			priv_string += "<warning> This user doesn't have usage privileges for this schema!"
		else:
			table_priv = self._db.connector.getTablePrivileges(self.name, self._schema.name if self._schema else None)
			privileges = []
			if table_priv[0]: privileges.append("select")
			if table_priv[1]: privileges.append("insert")
			if table_priv[2]: privileges.append("update")
			if table_priv[3]: privileges.append("delete")
			priv_string = u", ".join(privileges) if len(privileges) > 0 else u'<warning> This user has no privileges!'
		ret.append( ("Privileges:", priv_string ) )

		if table_priv[0] and not table_priv[1] and not table_priv[2] and not table_priv[3]:
			ret.append( (u'\n<warning> This user has read-only privileges.') )


		if not self.isView:
			if self.rowCount != None and (self.estimatedRowCount > 2 * self.rowCount or self.estimatedRowCount * 2 < self.rowCount):
				ret.append( (u"\n<warning> There's a significant difference between estimated and real row count. \n" \
					"Consider running VACUUM ANALYZE.") )

			if len( filter(lambda fld: fld.primaryKey, self.fields()) ) <= 0:
				ret.append( (u"\n<warning> No primary key defined for this table!") )

		return ret

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
		if self._fields == None:
			self._fields = map(lambda x: PGTableField(x, self), self._db.connector.getTableFields(self.name, self.schema().name if self.schema() else None))
		return self._fields

	def constraints(self):
		if self._constraints == None:
			self._constraints = map(lambda x: PGTableConstraint(x, self), self._db.connector.getTableConstraints(self.name, self.schema().name if self.schema() else None))
		return self._constraints

	def indexes(self):
		if self._indexes == None:
			self._indexes = map(lambda x: PGTableIndex(x, self), self._db.connector.getTableIndexes(self.name, self.schema().name if self.schema() else None))
		return self._indexes


class PGTableField(TableField):
	def __init__(self, row, table):
		TableField.__init__(self, table)
		self.num, self.name, self.dataType, self.charMaxLen, self.modifier, self.notNull, self.hasDefault, self.default = row
		self.primaryKey = False

		# find out whether fields are part of primary key
		for con in self._table.constraints():
			if con.type == PGTableConstraint.TypePrimaryKey and self.num in con.columns:
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

