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

from ..data_model import DbTableModel, DbSqlModel
from ..plugin import DbError


class PGTableModel(DbTableModel):
	def __init__(self, table, parent=None):
		self.cursor = None
		DbTableModel.__init__(self, table, parent)

		if self.table.rowCount == None:
			self.table.refreshRowCount()
			if self.table.rowCount == None:
				return

		fields_txt = ", ".join(self.fields)
		table_txt = self.db.quoteId( (self.table.schemaName(), self.table.name) )

		# create named cursor and run query
		self.cursor = self.db._get_cursor( table.name )
		sql = u"SELECT %s FROM %s" % (fields_txt, table_txt)
		self.cursor.execute(sql)

	def _sanitizeTableField(self, field):
		# get fields, ignore geometry columns
		if field.dataType.lower() == "geometry":
			#TODO use ST_GeometryType instead
			return u'GeometryType(%s)' % self.db.quoteId(field.name)
		return self.db.quoteId(field.name)


	def __del__(self):
		# close cursor and save memory
		if self.cursor:
			self.cursor.close()
		print "PGTableModel.__del__"

	def fetchMoreData(self, row_start):
		self.cursor.scroll(row_start, mode='absolute')
		self.resdata = self.cursor.fetchmany(self.fetchedCount)
		self.fetchedFrom = row_start


class PGSqlModel(DbSqlModel):
	def __init__(self, db, sql, parent=None):
		self.db = db.connector
		c = self.db._get_cursor()

		t = QTime()
		t.start()
		self.db._exec_sql(c, unicode(sql))
		self._secs = t.elapsed() / 1000.0
		del t

		data = []
		header = []
		if c.description:
			header = map(lambda x: x[0], c.description)
			try:
				data = self.db._fetchall(c)
			except DbError:
				# nothing to fetch!
				data = []
				header = []

		DbSqlModel.__init__(self, header, data, parent)

		# commit before closing the cursor to make sure that the changes are stored
		self.db.connection.commit()
		c.close()

	def secs(self):
		return self._secs


