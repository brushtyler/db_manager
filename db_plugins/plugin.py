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

from ..db_plugins import createDbPlugin
from .html_elems import HtmlParagraph, HtmlTable

class BaseException(Exception):
	def __init__(self, msg):
		try:
			self.msg = unicode( msg )
		except UnicodeDecodeError:
			self.msg = unicode( msg, 'utf-8' )
		Exception(self, self.msg)

	def __unicode__(self):
		return self.msg

	def __str__(self):
		return unicode(self).encode('utf-8')

class InvalidDataException(BaseException):
	pass

class ConnectionError(BaseException):
	pass

class DbError(BaseException):
	def __init__(self, ex, query=None):
		BaseException.__init__(self, ex.args[0])
		self.query = unicode( query ) if query else None

	def __unicode__(self):
		msg = u"Error:\n%s" % self.msg
		if self.query:
			msg += u"\n\nQuery:\n%s" % self.query
		return msg



class DBPlugin(QObject):
	def __init__(self, conn_name, parent=None):
		QObject.__init__(self, parent)
		self.connName = conn_name
		self.db = None

	def __del__(self):
		pass	#print "DBPlugin.__del__", self.connName

	def connectionName(self):
		return self.connName

	def database(self):
		return self.db

	def info(self):
		from .info_model import DatabaseInfo
		return DatabaseInfo(None)

	def connect(self, uri):
		self.db = self.databasesFactory( self, uri )
		if self.db: 
			return True
		return False

	@classmethod
	def icon(self):
		return None

	@classmethod
	def typeName(self):
		# return the db typename (e.g. 'postgis')
		pass

	@classmethod
	def typeNameString(self):
		# return the db typename string (e.g. 'PostGIS')
		pass

	@classmethod
	def providerName(self):
		# return the provider's name (e.g. 'postgres')
		pass

	@classmethod
	def connectionSettingsKey(self):
		# return the key used to store the connections in settings
		pass

	@classmethod
	def connections(self):
		# get the list of connections
		conn_list = []
		settings = QSettings()
		settings.beginGroup( self.connectionSettingsKey() )
		for name in settings.childGroups():
			conn_list.append( createDbPlugin(self.typeName(), name) )
		settings.endGroup()
		return conn_list


	def databasesFactory(self, connection, uri):
		return None 


class DbItemObject(QObject):
	def __init__(self, parent=None):
		QObject.__init__(self, parent)

	def database(self):
		return None

	def refresh(self):
		self.emit( SIGNAL('changed') )	# refresh the item data reading them from the db

	def info(self):
		pass

	def runAction(self):
		pass

	def registerActions(self, mainWindow):
		pass


class Database(DbItemObject):
	def __init__(self, dbplugin, uri):
		DbItemObject.__init__(self, dbplugin)
		self.connector = self.connectorsFactory( uri )

	def connectorsFactory(self, uri):
		return None

	def __del__(self):
		self.connector = None
		pass	#print "Database.__del__", self

	def connection(self):
		return self.parent()

	def dbplugin(self):
		return self.parent()

	def database(self):
		return self

	def uri(self):
		return self.connector.uri()

	def publicUri(self):
		return self.connector.publicUri()

	def info(self):
		from .info_model import DatabaseInfo
		return DatabaseInfo(self)


	def sqlResultModel(self, sql, parent):
		from .data_model import SqlResultModel
		return SqlResultModel(self, sql, parent)


	def toSqlLayer(self, sql, geomCol, uniqueCol, layerName="QueryLayer", layerType=None):
		from qgis.core import QgsMapLayer, QgsVectorLayer, QgsRasterLayer
		uri = self.uri()
		uri.setDataSource("", u"(%s\n)" % sql, geomCol, QString(), uniqueCol)
		provider = self.dbplugin().providerName()
		if layerType == QgsMapLayer.RasterLayer:
			return QgsRasterLayer(uri.uri(), layerName, provider)
		return QgsVectorLayer(uri.uri(), layerName, provider)


	def registerAllActions(self, mainWindow):
		self.registerDatabaseActions(mainWindow)
		self.registerSubPluginActions(mainWindow)

	def registerSubPluginActions(self, mainWindow):
		# load plugins!
		try:
			exec( u"from .%s.plugins import load" % self.dbplugin().typeName() )
		except ImportError:
			pass
		else:
			load(self, mainWindow)

	def registerDatabaseActions(self, mainWindow):
		if self.schemas() != None:
			action = QAction("&Create schema", self)
			mainWindow.registerAction( action, "&Schema", self.createSchemaActionSlot )
			action = QAction("&Delete (empty) schema", self)
			mainWindow.registerAction( action, "&Schema", self.deleteSchemaActionSlot )

		action = QAction("Delete selected item", self)
		mainWindow.registerAction( action, None, self.deleteActionSlot )
		action.setShortcuts(QKeySequence.Delete)

		action = QAction(QIcon(":/db_manager/actions/create_table"), "&Create table", self)
		mainWindow.registerAction( action, "&Table", self.createTableActionSlot )
		action = QAction(QIcon(":/db_manager/actions/edit_table"), "&Edit table", self)
		mainWindow.registerAction( action, "&Table", self.editTableActionSlot )
		action = QAction(QIcon(":/db_manager/actions/del_table"), "&Delete table/view", self)
		mainWindow.registerAction( action, "&Table", self.deleteTableActionSlot )
		action = QAction("&Empty table", self)
		mainWindow.registerAction( action, "&Table", self.emptyTableActionSlot )

	def deleteActionSlot(self, item, action, parent):
		if isinstance(item, Schema):
			self.deleteSchemaActionSlot(item, action, parent)
		elif isinstance(item, Table):
			self.deleteTableActionSlot(item, action, parent)
		else:
			QMessageBox.information(parent, "Sorry", "Cannot delete the selected item.")

	def createSchemaActionSlot(self, item, action, parent):
		if not isinstance(item, (DBPlugin, Schema, Table)) or item.database() == None:
			QMessageBox.information(parent, "Sorry", "No database selected or you are not connected to it.")
			return
		(schema, ok) = QInputDialog.getText(parent, "New schema", "Enter new schema name")
		if not ok:
			return
		self.createSchema(schema)

	def deleteSchemaActionSlot(self, item, action, parent):
		if not isinstance(item, Schema):
			QMessageBox.information(parent, "Sorry", "Select an empty SCHEMA for deletion.")
			return
		res = QMessageBox.question(parent, "hey!", u"Really delete schema %s ?" % item.name, QMessageBox.Yes | QMessageBox.No)
		if res != QMessageBox.Yes:
			return
		item.delete()


	def schemasFactory(self, row, db):
		return None

	def schemas(self):
		schemas = self.connector.getSchemas()
		if schemas != None:
			schemas = map(lambda x: self.schemasFactory(x, self), schemas)
		return schemas

	def createSchema(self, name):
		self.connector.createSchema(name)
		self.refresh()


	def createTableActionSlot(self, item, action, parent):
		if not hasattr(item, 'database') or item.database() == None:
			QMessageBox.information(parent, "Sorry", "No database selected or you are not connected to it.")
			return
		from ..dlg_create_table import DlgCreateTable
		DlgCreateTable(item, parent).exec_()

	def editTableActionSlot(self, item, action, parent):
		if not isinstance(item, Table):
			QMessageBox.information(parent, "Sorry", "Select a TABLE for editation.")
			return
		from ..dlg_table_properties import DlgTableProperties
		DlgTableProperties(item, parent).exec_()

	def deleteTableActionSlot(self, item, action, parent):
		if not isinstance(item, Table):
			QMessageBox.information(parent, "Sorry", "Select a TABLE/VIEW for deletion.")
			return
		res = QMessageBox.question(parent, "hey!", u"Really delete table/view %s ?" % item.name, QMessageBox.Yes | QMessageBox.No)
		if res != QMessageBox.Yes:
			return
		item.delete()

	def emptyTableActionSlot(self, item, action, parent):
		if not isinstance(item, Table) or item.isView:
			QMessageBox.information(parent, "Sorry", "Select a TABLE to empty it.")
			return
		res = QMessageBox.question(parent, "hey!", u"Really delete all items from table %s ?" % item.name, QMessageBox.Yes | QMessageBox.No)
		if res != QMessageBox.Yes:
			return
		item.empty()


	def tablesFactory(self, row, db, schema=None):
		typ, row = row[0], row[1:]
		if typ == Table.VectorType:
			return self.vectorTablesFactory(row, db, schema)
		elif typ == Table.RasterType:
			return self.rasterTablesFactory(row, db, schema)
		return self.dataTablesFactory(row, db, schema)

	def dataTablesFactory(self, row, db, schema=None):
		return None

	def vectorTablesFactory(self, row, db, schema=None):
		return None

	def rasterTablesFactory(self, row, db, schema=None):
		return None

	def tables(self, schema=None):
		tables = self.connector.getTables(schema.name if schema else None)
		if tables != None:
			tables = map(lambda x: self.tablesFactory(x, self, schema), tables)
		return tables

	def createTable(self, table, fields, schema=None):
		field_defs = map( lambda x: x.definition(), fields )
		pkeys = filter(lambda x: x.primaryKey, fields)
		pk_name = pkeys[0].name if len(pkeys) > 0 else None

		ret = self.connector.createTable( (schema, table), field_defs, pk_name)
		if ret != False:
			self.refresh()
		return ret

	def createVectorTable(self, table, fields, geom, schema=None):
		ret = self.createTable( (schema, table), fields)
		if ret == False:
			return False

		try:
			createGeomCol = geom != None
			if createGeomCol:
				geomCol, geomType, geomSrid, geomDim = geom[:4]
				createSpatialIndex = geom[4] == True if len(geom) > 4 else False

				self.connector.addGeometryColumn( (schema, table), geomType, geomCol, geomSrid, geomDim)

				if createSpatialIndex:
					# commit data definition changes, otherwise index can't be built
					self.connector._commit()
					self.connector.createSpatialIndex( (schema, table), geomCol)

		finally:
			self.refresh()
		return True


class Schema(DbItemObject):
	def __init__(self, db):
		DbItemObject.__init__(self, db)
		self.oid = self.name = self.owner = self.perms = None
		self.comment = None
		self.tableCount = 0

	def __del__(self):
		pass	#print "Schema.__del__", self

	def database(self):
		return self.parent()

	def schema(self):
		return self

	def tables(self):
		return self.database().tables(self)

	def delete(self):
		ret = self.database().connector.deleteSchema(self.name)
		if ret != False:
			self.emit( SIGNAL('deleted') )
		return ret

	def rename(self, new_name):
		ret = self.database().connector.renameSchema(self.name, new_name)
		if ret != False:
			self.refresh()
		return ret

	def info(self):
		from .info_model import SchemaInfo
		return SchemaInfo(self)


class Table(DbItemObject):
	TableType, VectorType, RasterType = range(3)

	def __init__(self, db, schema=None, parent=None):
		DbItemObject.__init__(self, db)
		self._schema = schema
		if hasattr(self, 'type'):
			return
		self.type = Table.TableType

		self.name = self.isView = self.owner = self.pages = None
		self.comment = None
		self.rowCount = None

		self._fields = self._indexes = self._constraints = self._triggers = self._rules = None

	def __del__(self):
		pass	#print "Table.__del__", self

	def database(self):
		return self.parent()

	def schema(self):
		return self._schema

	def schemaName(self):
		return self.schema().name if self.schema() else None

	def quotedName(self):
		return self.database().connector.quoteId( (self.schemaName(), self.name) )


	def delete(self):
		if self.isView:
			ret = self.database().connector.deleteView( (self.schemaName(), self.name) )
		else:
			ret = self.database().connector.deleteTable( (self.schemaName(), self.name) )
		if ret != False: 
			self.emit( SIGNAL('deleted') )
		return ret

	def rename(self, new_name):
		ret = self.database().connector.renameTable( (self.schemaName(), self.name), new_name)
		if ret != False:
			self.name = new_name
			self.refresh()
		return ret

	def empty(self):
		ret = self.database().connector.emptyTable( (self.schemaName(), self.name) )
		if ret != False:
			self.refreshRowCount()
		return ret

	def info(self):
		from .info_model import TableInfo
		return TableInfo(self)

	def uri(self):
		uri = self.database().uri()
		schema = self.schemaName() if self.schemaName() else ''
		geomCol = self.geomColumn if self.type in [Table.VectorType, Table.RasterType] else QString()
		pk = self.getValidQGisUniqueFields(True)
		uri.setDataSource(schema, self.name, geomCol if geomCol else QString(), QString(), pk.name if pk else QString())
		return uri

	def mimeUri(self):
		layerType = "raster" if self.type == Table.RasterType else "vector"
		return u"%s:%s:%s:%s" % (layerType, self.database().dbplugin().providerName(), self.name, self.uri().uri())

	def toMapLayer(self):
		from qgis.core import QgsVectorLayer, QgsRasterLayer
		provider = self.database().dbplugin().providerName()
		uri = self.uri().uri()
		if self.type == Table.RasterType:
			return QgsRasterLayer(uri, self.name, provider)
		return QgsVectorLayer(uri, self.name, provider)

	def getValidQGisUniqueFields(self, onlyOne=False):
		""" list of fields valid to load the table as layer in qgis canvas """
		ret = []

		# add the pk
		pkcols = filter(lambda x: x.primaryKey, self.fields())
		if len(pkcols) == 1: ret.append( pkcols[0] )

		# add both serial and int4 fields with an unique index
		indexes = self.indexes()
		if indexes != None:
			for idx in indexes:
				if idx.isUnique and len(idx.columns) == 1:
					fld = idx.fields()[ idx.columns[0] ]
					if fld and fld not in ret and fld.dataType in ["oid", "serial", "int4"]:
						ret.append( fld )

		if onlyOne:
			return ret[0] if len(ret) > 0 else None
		return ret


	def tableDataModel(self, parent):
		pass


	def tableFieldsFactory(self):
		return None

	def fields(self):
		if self._fields == None:
			fields = self.database().connector.getTableFields( (self.schemaName(), self.name) )
			if fields != None:
				self._fields = map(lambda x: self.tableFieldsFactory(x, self), fields)
		return self._fields

	def refreshFields(self):
		self._fields = None	# refresh table fields
		self.refresh()

	def addField(self, fld):
		ret = self.database().connector.addTableColumn( (self.schemaName(), self.name), fld.definition())
		if ret != False:
			self.refreshFields()
		return ret

	def deleteField(self, fld):
		ret = self.database().connector.deleteTableColumn( (self.schemaName(), self.name), fld.name)
		if ret != False:
			self.refreshFields()
		return ret

	def renameField(self, fld, new_name):
		ret = self.database().connector.renameTableColumn( (self.schemaName(), self.name), fld.name, new_name)
		if ret != False:
			self.refreshFields()
		return ret

	def addGeometryColumn(self, geomCol, geomType, srid, dim, createSpatialIndex=False):
		ret = self.database().connector.addGeometryColumn( (self.schemaName(), self.name), geomType, geomCol, srid, dim)
		if ret == False:
			return False

		try:
			if createSpatialIndex:
				# commit data definition changes, otherwise index can't be built
				self.database().connector._commit()
				self.database().connector.createSpatialIndex( (self.schemaName(), self.name), geomCol)

		finally:
			self.schema().refreshTables()	# another table was added to the schema
		return True


	def tableConstraintsFactory(self):
		return None

	def constraints(self):
		if self._constraints == None:
			constraints = self.database().connector.getTableConstraints( (self.schemaName(), self.name) )
			if constraints != None:
				self._constraints = map(lambda x: self.tableConstraintsFactory(x, self), constraints)
		return self._constraints

	def refreshConstraints(self):
		self._constraints = None	# refresh table constraints
		self.refresh()

	def addConstraint(self, constr):
		if constr.type == TableConstraint.TypePrimaryKey:
			ret = self.database().connector.addTablePrimaryKey( (self.schemaName(), self.name), constr.fields()[constr.columns[0]].name)
		elif constr.type == TableConstraint.TypeUnique:
			ret = self.database().connector.addTableUniqueConstraint( (self.schemaName(), self.name), constr.fields()[constr.columns[0]].name)
		else:
			return False
		if ret != False:
			self.refreshConstraints()
		return ret

	def deleteConstraint(self, constr):
		ret = self.database().connector.deleteTableConstraint( (self.schemaName(), self.name), constr.name)
		if ret != False:
			self.refreshConstraints()
		return ret


	def tableIndexesFactory(self):
		return None

	def indexes(self):
		if self._indexes == None:
			indexes = self.database().connector.getTableIndexes( (self.schemaName(), self.name) )
			if indexes != None:
				self._indexes = map(lambda x: self.tableIndexesFactory(x, self), indexes)
		return self._indexes

	def refreshIndexes(self):
		self._indexes = None	# refresh table indexes
		self.refresh()

	def addIndex(self, idx):
		ret = self.database().connector.addTableIndex( (self.schemaName(), self.name), idx.name, idx.fields()[idx.columns[0]].name)
		if ret != False:
			self.refreshIndexes()
		return ret

	def deleteIndex(self, idx):
		ret = self.database().connector.deleteTableIndex( (self.schemaName(), self.name), idx.name)
		if ret != False:
			self.refreshIndexes()
		return ret


	def tableTriggersFactory(self, row, table):
		return None

	def triggers(self):
		if self._triggers == None:
			triggers = self.database().connector.getTableTriggers( (self.schemaName(), self.name) )
			if triggers != None:
				self._triggers = map(lambda x: self.tableTriggersFactory(x, self), triggers)
		return self._triggers

	def refreshTriggers(self):
		self._triggers = None	# refresh table triggers
		self.refresh()


	def tableRulesFactory(self, row, table):
		return None

	def rules(self):
		if self._rules == None:
			rules = self.database().connector.getTableRules( (self.schemaName(), self.name) )
			if rules != None:
				self._rules = map(lambda x: self.tableRulesFactory(x, self), rules)
		return self._rules

	def refreshRules(self):
		self._rules = None	# refresh table rules
		self.refresh()


	def refreshRowCount(self):
		try:
			self.rowCount = self.database().connector.getTableRowCount( (self.schemaName(), self.name) )
			self.rowCount = int(self.rowCount) if self.rowCount != None else None
		except DbError:
			self.rowCount = None
		self.refresh()


	def runAction(self, action):
		action = unicode(action)

		if action.startswith( "rows/" ):
			if action == "rows/count":
				self.refreshRowCount()
				return True

		elif action.startswith( "triggers/" ):
			parts = action.split('/')
			trigger_action = parts[1]

			msg = u"Do you want to %s all triggers?" % trigger_action
			if QMessageBox.question(None, "Table triggers", msg, QMessageBox.Yes|QMessageBox.No) == QMessageBox.No:
				return False

			if trigger_action == "enable" or trigger_action == "disable":
				enable = trigger_action == "enable"
				self.database().connector.enableAllTableTriggers(enable, (self.schemaName(), self.name) )
				self.refreshTriggers()
				return True

		elif action.startswith( "trigger/" ):
			parts = action.split('/')
			trigger_name = parts[1]
			trigger_action = parts[2]

			msg = u"Do you want to %s trigger %s?" % (trigger_action, trigger_name)
			if QMessageBox.question(None, "Table trigger", msg, QMessageBox.Yes|QMessageBox.No) == QMessageBox.No:
				return False

			if trigger_action == "delete":
				self.database().connector.deleteTableTrigger(trigger_name, (self.schemaName(), self.name) )
				self.refreshTriggers()
				return True

			elif trigger_action == "enable" or trigger_action == "disable":
				enable = trigger_action == "enable"
				self.database().connector.enableTableTrigger(trigger_name, enable, (self.schemaName(), self.name) )
				self.refreshTriggers()
				return True

		return False

class VectorTable(Table):
	def __init__(self, db, schema=None, parent=None):
		if not hasattr(self, 'type'):	# check if the superclass constructor was called yet!
			Table.__init__(self, db, schema, parent)
		self.type = Table.VectorType
		self.geomColumn = self.geomType = self.geomDim = self.srid = None

	def info(self):
		from .info_model import VectorTableInfo
		return VectorTableInfo(self)

	def createSpatialIndex(self, geom_column):
		ret = self.database().connector.createSpatialIndex( (self.schemaName(), self.name), geom_column)
		if ret != False:
			self.refreshIndexes()
		return ret

class RasterTable(Table):
	def __init__(self, db, schema=None, parent=None):
		if not hasattr(self, 'type'):	# check if the superclass constructor was called yet!
			Table.__init__(self, db, schema, parent)
		self.type = Table.RasterType
		self.geomColumn = self.geomType = self.pixelSizeX = self.pixelSizeY = self.pixelType = self.isExternal = self.srid = None

	def info(self):
		from .info_model import RasterTableInfo
		return RasterTableInfo(self)


class TableSubItemObject(QObject):
	def __init__(self, table):
		QObject.__init__(self, table)

	def table(self):
		return self.parent()

	def database(self):
		return self.table().database() if self.table() else None


class TableField(TableSubItemObject):
	def __init__(self, table):
		TableSubItemObject.__init__(self, table)
		self.num = self.name = self.dataType = self.modifier = self.notNull = self.default = self.hasDefault = self.primaryKey = None
		self.comment = None

	def type2String(self):
		if self.modifier == None or self.modifier == -1:
			return u"%s" % self.dataType
		return u"%s (%s)" % (self.dataType, self.modifier)

	def default2String(self):
		if not self.hasDefault:
			return ''
		return self.default if self.default != None else "NULL"

	def definition(self):
		from .connector import DBConnector
		quoteIdFunc = self.database().connector.quoteId if self.database() else DBConnector.quoteId

		name = quoteIdFunc(self.name)
		not_null = "NOT NULL" if self.notNull else ""

		txt = u"%s %s %s" % (name, self.type2String(), not_null)
		if self.hasDefault:
			txt += u" DEFAULT %s" % self.default2String()
		return txt

	def delete(self):
		return self.table().deleteField(self)

	def rename(self, new_name):
		return self.table().renameField(self, new_name)

class TableConstraint(TableSubItemObject):
	""" class that represents a constraint of a table (relation) """
	
	TypeCheck, TypeForeignKey, TypePrimaryKey, TypeUnique = range(4)
	types = { "c" : TypeCheck, "f" : TypeForeignKey, "p" : TypePrimaryKey, "u" : TypeUnique }
	
	onAction = { "a" : "NO ACTION", "r" : "RESTRICT", "c" : "CASCADE", "n" : "SET NULL", "d" : "SET DEFAULT" }
	matchTypes = { "u" : "UNSPECIFIED", "f" : "FULL", "p" : "PARTIAL" }

	def __init__(self, table):
		TableSubItemObject.__init__(self, table)
		self.name = self.type = self.columns = None

	def type2String(self):
		if self.type == TableConstraint.TypeCheck: return "Check"
		if self.type == TableConstraint.TypePrimaryKey: return "Primary key"
		if self.type == TableConstraint.TypeForeignKey: return "Foreign key"
		if self.type == TableConstraint.TypeUnique: return "Unique"
		return 'Unknown'

	def fields(self):
		def fieldFromNum(num, fields):
			""" return field specified by its number or None if doesn't exist """
			for fld in fields:
				if fld.num == num:
					return fld
			return None

		fields = self.table().fields()
		cols = {}
		for num in self.columns:
			cols[num] = fieldFromNum(num, fields)
		return cols

	def delete(self):
		return self.table().deleteConstraint(self)


class TableIndex(TableSubItemObject):
	def __init__(self, table):
		TableSubItemObject.__init__(self, table)
		self.name = self.columns = self.isUnique = None

	def fields(self):
		def fieldFromNum(num, fields):
			""" return field specified by its number or None if doesn't exist """
			for fld in fields:
				if fld.num == num: return fld
			return None

		fields = self.table().fields()
		cols = {}
		for num in self.columns:
			cols[num] = fieldFromNum(num, fields)
		return cols

	def delete(self):
		return self.table().deleteIndex(self)


class TableTrigger(TableSubItemObject):
	""" class that represents a trigger """
	
	# Bits within tgtype (pg_trigger.h)
	TypeRow      = (1 << 0) # row or statement
	TypeBefore   = (1 << 1) # before or after
	# events: one or more
	TypeInsert   = (1 << 2)
	TypeDelete   = (1 << 3)
	TypeUpdate   = (1 << 4)
	TypeTruncate = (1 << 5)

	def __init__(self, table):
		TableSubItemObject.__init__(self, table)
		self.name = self.function = None

	def type2String(self):
		trig_type = u''
		trig_type += "Before " if self.type & TableTrigger.TypeBefore else "After "
		if self.type & TableTrigger.TypeInsert: trig_type += "INSERT "
		if self.type & TableTrigger.TypeUpdate: trig_type += "UPDATE "
		if self.type & TableTrigger.TypeDelete: trig_type += "DELETE "
		if self.type & TableTrigger.TypeTruncate: trig_type += "TRUNCATE "
		trig_type += "\n"
		trig_type += "for each "
		trig_type += "row" if self.type & TableTrigger.TypeRow else "statement"
		return trig_type


class TableRule(TableSubItemObject):
	def __init__(self, table):
		TableSubItemObject.__init__(self, table)
		self.name = self.definition = None
 
