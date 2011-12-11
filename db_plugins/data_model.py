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


class BaseTableModel(QAbstractTableModel):
	def __init__(self, header=None, data=None, parent=None):
		QAbstractTableModel.__init__(self, parent)
		self._header = header if header else []
		self.resdata = data if data else []

	def getData(self, row, col):
		return self.resdata[row][col]

	def columnNames(self):
		return list(self._header)

	def rowCount(self, parent=None):
		return len(self.resdata)

	def columnCount(self, parent=None):
		return len(self._header)
	
	def data(self, index, role):
		if role != Qt.DisplayRole and role != Qt.FontRole:
			return QVariant()
		
		val = self.getData(index.row(), index.column())

		if role == Qt.FontRole:	# draw NULL in italic
			if val != None:
				return QVariant()
			f = QFont()
			f.setItalic(True)
			return QVariant(f)

		if val == None:
			return QVariant("NULL")
		else:
			return QVariant(val)		
	
	def headerData(self, section, orientation, role):
		if role != Qt.DisplayRole:
			return QVariant()
		
		if orientation == Qt.Vertical:
			# header for a row
			return QVariant(section+1)
		else:
			# header for a column
			return QVariant(self._header[section])


class TableDataModel(BaseTableModel):
	def __init__(self, table, parent=None):
		self.db = table.database().connector
		self.table = table

		fieldNames = map(lambda x: x.name, table.fields())
		BaseTableModel.__init__(self, fieldNames, None, parent)

		# get table fields
		self.fields = []
		for fld in table.fields():
			self.fields.append( self._sanitizeTableField(fld) )

		self.fetchedCount = 201
		self.fetchedFrom = -self.fetchedCount-1		# so the first call to getData will exec fetchMoreData(0)

	def _sanitizeTableField(self, field):
		""" quote column names to avoid some problems (e.g. columns with upper case) """
		return self.db.quoteId(field)

	def getData(self, row, col):
		if row < self.fetchedFrom or row >= self.fetchedFrom + self.fetchedCount:
			margin = self.fetchedCount/2
			start = self.rowCount() - margin if row + margin >= self.rowCount() else row - margin
			if start < 0: start = 0
			self.fetchMoreData(start)
		return self.resdata[row-self.fetchedFrom][col]

	def fetchMoreData(self, row_start):
		pass

	def rowCount(self, index=None):
		# case for tables with no columns ... any reason to use them? :-)
		return self.table.rowCount if self.table.rowCount != None and self.columnCount(index) > 0 else 0


class SqlResultModel(BaseTableModel):
	def __init__(self, db, sql, parent=None):
		self.db = db.connector
		c = self.db._get_cursor()

		t = QTime()
		t.start()
		self.db._execute(c, unicode(sql))
		self._secs = t.elapsed() / 1000.0
		del t

		self._affectedRows = 0
		data = []
		try:
			header = self.db._get_columns(c)
			if len(header) > 0:
				data = self.db._fetchall(c)
			self._affectedRows = c.rowcount
		except DbError:
			# nothing to fetch!
			data = []
			header = []

		BaseTableModel.__init__(self, header, data, parent)

		# commit before closing the cursor to make sure that the changes are stored
		self.db._commit()
		c.close()
		del c

	def secs(self):
		return self._secs

	def affectedRows(self):
		return self._affectedRows



class SimpleTableModel(QStandardItemModel):
	def __init__(self, header, parent=None):
		self.header = header
		QStandardItemModel.__init__(self, 0, len(self.header), parent)

	@classmethod
	def rowFromData(self, data):
		row = []
		for c in data:
			row.append( QStandardItem(unicode(c)) )
		return row

	def headerData(self, section, orientation, role):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			return QVariant(self.header[section])
		return QVariant()


class TableFieldsModel(SimpleTableModel):
	def __init__(self, parent):
		SimpleTableModel.__init__(self, ['Name', 'Type', 'Null', 'Default'], parent)

	def headerData(self, section, orientation, role):
		if orientation == Qt.Vertical and role == Qt.DisplayRole:
			return QVariant(section+1)
		return SimpleTableModel.headerData(self, section, orientation, role)


	def appendField(self, fld):
		data = [fld.name, fld.type2String(), not fld.notNull, fld.default2String()]
		self.appendRow( self.rowFromData(data) )
		row = self.rowCount()-1
		self.setData(self.index(row, 0), QVariant(fld.primaryKey), Qt.UserRole)

	def getFields(self):
		from .plugin import TableField
		flds = []
		for row in range(self.rowCount()):
			fld = TableField(None)
			fld.name = self.data(self.index(row, 0)).toString()
			fld.dataType = self.data(self.index(row, 1)).toString()
			fld.notNull = not self.data(self.index(row, 2)).toBool()
			fld.primaryKey = self.data(self.index(row, 0), Qt.UserRole).toBool()
			flds.append( fld )
		return flds


class TableConstraintsModel(SimpleTableModel):
	def __init__(self, parent):
		SimpleTableModel.__init__(self, parent, ['Name', 'Type', 'Column(s)'])

	def appendConstraint(self, constr):
		field_names = map( lambda x,y: y.name, constr.fields() )
		self.appendData( [constr.name, constr.type2String(), u", ".join(field_names)] )

	def getConstraints(self, db):
		from .plugin import TableConstraint
		constrs = []
		for row in range(self.rowCount()):
			constr = TableConstraint(None, db)
			constr.name = self.data(self.index(row, 0)).toString()
			constr.type = self.data(self.index(row, 1)).toString()
			constrs.append( constr )
		return constrs


class TableIndexesModel(SimpleTableModel):
	def __init__(self, parent):
		SimpleTableModel.__init__(self, parent, ['Name', 'Column(s)'])

	def appendIndex(self, idx):
		field_names = map( lambda x,y: y.name, idx.fields() )
		self.appendData( [idx.name, u", ".join(field_names)] )

