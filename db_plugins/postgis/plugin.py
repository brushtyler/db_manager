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

from ..plugin import DBPlugin, Database, Schema, Table, TableField, TableConstraint, TableIndex
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

	def databasesFactory(self, connection, uri):
		return PGDatabase(connection, uri)

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
		uri = qgis.core.QgsDataSourceURI()
		uri.setConnection(host, port, database, username, password)
		self.db = self.databasesFactory( self, uri )
		return True


class PGDatabase(Database):
	def __init__(self, connection, uri):
		Database.__init__(self, connection, uri)

	def connectorsFactory(self, uri):
		from .connector import PostGisDBConnector
		return PostGisDBConnector(uri)

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


	def tablesFactory(self, row, db, schema=None):
		return PGTable(row, db, schema)

	def schemasFactory(self, row, db):
		return PGSchema(row, db)


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
		details = self.database().connector.getSchemaPrivileges(self.name)
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
		# has the user access to this schema?
		schema_priv = self._schema.privilegesDetails() if self._schema else None
		if schema_priv == None:
			pass
		elif len(schema_priv) <= 0:
			priv_string = u"<warning> This user doesn't have usage privileges for this schema!"
			ret.append( ("Privileges:", priv_string ) )
		else:
			privileges = self.privilegesDetails()
			priv_string = u", ".join(privileges) if len(privileges) > 0 else u'<warning> This user has no privileges!'
			ret.append( ("Privileges:", priv_string ) )

			table_priv = self.database().connector.getTablePrivileges(self.name, self.schema().name if self.schema() else None)
			if table_priv[0] and not table_priv[1] and not table_priv[2] and not table_priv[3]:
				ret.append( (u"\n<warning> This user has read-only privileges.") )

		if not self.isView:
			if self.rowCount != None and (self.estimatedRowCount > 2 * self.rowCount or self.estimatedRowCount * 2 < self.rowCount):
				ret.append( (u"\n<warning> There's a significant difference between estimated and real row count. \n" \
					"Consider running VACUUM ANALYZE.") )

		if not self.isView:
			if len( filter(lambda fld: fld.primaryKey, self.fields()) ) <= 0:
				ret.append( (u"\n<warning> No primary key defined for this table!") )

		return ret

	def privilegesDetails(self):
		details = self.database().connector.getTablePrivileges(self.name, self.schema().name if self.schema() else None)
		ret = []
		if details[0]: ret.append("select")
		if details[1]: ret.append("insert")
		if details[2]: ret.append("update")
		if details[3]: ret.append("delete")
		return ret


	def fieldsDetails(self):
		pass


	def tableFieldsFactory(self, row, table):
		return PGTableField(row, table)

	def tableConstraintsFactory(self, row, table):
		return PGTableConstraint(row, table)

	def tableIndexesFactory(self, row, table):
		return PGTableIndex(row, table)



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

