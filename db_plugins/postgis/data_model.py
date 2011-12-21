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

from ..data_model import TableDataModel, SqlResultModel
from ..plugin import DbError


class PGTableDataModel(TableDataModel):
	def __init__(self, table, parent=None):
		self.cursor = None
		TableDataModel.__init__(self, table, parent)

		if self.table.rowCount == None:
			self.table.refreshRowCount()
			if self.table.rowCount == None:
				return
		self._createCursor()

	def _createCursor(self):
		fields_txt = u", ".join(self.fields)
		table_txt = self.db.quoteId( (self.table.schemaName(), self.table.name) )

		# create named cursor and run query
		self.cursor = self.db._get_cursor(self.table.name)
		sql = u"SELECT %s FROM %s" % (fields_txt, table_txt)
		self.db._execute(self.cursor, sql)

	def _sanitizeTableField(self, field):
		# get fields, ignore geometry columns
		if field.dataType.lower() == "geometry":
			return u"CASE WHEN %(fld)s IS NULL THEN NULL ELSE GeometryType(%(fld)s) END AS %(fld)s" % {'fld': self.db.quoteId(field.name)}
		elif field.dataType.lower() == "raster":
			return u"CASE WHEN %(fld)s IS NULL THEN NULL ELSE 'RASTER' END AS %(fld)s" % {'fld': self.db.quoteId(field.name)}
		return u"%s::text" % self.db.quoteId(field.name)


	def __del__(self):
		# close cursor and save memory
		self.cursor.close()
		del self.cursor
		pass	#print "PGTableModel.__del__"

	def fetchMoreData(self, row_start):
		try:
			self.cursor.scroll(row_start, mode='absolute')
		except self.db.connector._error_types():
			self.cursor.close()
			del self.cursor
			self._createCursor()
			return self.fetchMoreData(row_start)

		self.resdata = self.cursor.fetchmany(self.fetchedCount)
		self.fetchedFrom = row_start


class PGSqlResultModel(SqlResultModel):
	pass

