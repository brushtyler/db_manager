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
		self.header = header if header else []
		self.resdata = data if data else []

	def getData(self, row, col):
		return self.resdata[row][col]
		
	def rowCount(self, parent=None):
		return len(self.resdata)
	
	def columnCount(self, parent):
		return len(self.header)
	
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
			return QVariant(self.header[section])


class DbTableModel(BaseTableModel):
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


class DbSqlModel(BaseTableModel):
	def __init__(self, header, data, parent=None):
		BaseTableModel.__init__(self, header, data, parent)

	def secs(self):
		pass


