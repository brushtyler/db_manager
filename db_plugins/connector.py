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

from qgis.core import QgsDataSourceURI

from .plugin import DbError

class DBConnector:
	def __init__(self, uri):
		self.connection = None
		self._uri = uri

	def __del__(self):
		pass	#print "DBConnector.__del__", self._uri.connectionInfo()
		if self.connection != None: 
			self.connection.close()
		self.connection = None


	def uri(self):
		return QgsDataSourceURI( self._uri.uri() )

	def publicUri(self):
		publicUri = QgsDataSourceURI.removePassword( self._uri.uri() )
		return QgsDataSourceURI( publicUri )


	def hasCustomQuerySupport(self):
		return False


	def _error_types():
		raise Exception("DBConnector._error_types() is an abstract method")

	def _execute(self, cursor, sql):
		if cursor == None:
			cursor = self._get_cursor()
		try:
			cursor.execute(unicode(sql))
		except self._error_types(), e:
			# do the rollback to avoid a "current transaction aborted, commands ignored" errors
			self._rollback()
			raise DbError(e, sql)
		return cursor
		
	def _execute_and_commit(self, sql):
		""" tries to execute and commit some action, on error it rolls back the change """
		c = self.connection.cursor()
		self._execute(c, sql)
		self._commit()

	def _get_cursor(self, name=None):
		if name:
			name = QString( unicode(name).encode('ascii', 'replace') ).replace( QRegExp("\W"), "_" ).toAscii()
			self._last_cursor_named_id = 0 if not hasattr(self, '_last_cursor_named_id') else self._last_cursor_named_id + 1
			return self.connection.cursor( "%s_%d" % (name, self._last_cursor_named_id) )
		return self.connection.cursor()

	def _fetchall(self, c):
		try:
			return c.fetchall()
		except self._error_types(), e:
			# do the rollback to avoid a "current transaction aborted, commands ignored" errors
			self._rollback()
			raise DbError(e)

	def _fetchone(self, c):
		try:
			return c.fetchone()
		except self._error_types(), e:
			# do the rollback to avoid a "current transaction aborted, commands ignored" errors
			self._rollback()
			raise DbError(e)

	def _commit(self):
		self.connection.commit()

	def _rollback(self):
		self.connection.rollback()

	def _get_cursor_columns(self, c):
		if c.description:
			return map(lambda x: x[0], c.description)
		return []


	@classmethod
	def quoteId(self, identifier):
		if hasattr(identifier, '__iter__'):
			ids = list()
			for i in identifier:
				if i == None:
					continue
				ids.append( self.quoteId(i) )
			return u'.'.join( ids )

		identifier = unicode(identifier) if identifier != None else unicode() # make sure it's python unicode string
		return u'"%s"' % identifier.replace('"', '""')
	
	@classmethod
	def quoteString(self, txt):
		""" make the string safe - replace ' with '' """
		if hasattr(txt, '__iter__'):
			txts = list()
			for i in txt:
				if i == None:
					continue
				txts.append( self.quoteString(i) )
			return u'.'.join( txts )

		txt = unicode(txt) if txt != None else unicode() # make sure it's python unicode string
		return u"'%s'" % txt.replace("'", "''")

	@classmethod
	def getSchemaTableName(self, table):
		if not hasattr(table, '__iter__'):
			return (None, table)
		elif len(table) < 2:
			return (None, table[0])
		else:
			return (table[0], table[1])


	def createTable(self, table, field_defs, pkey):
		""" create ordinary table
				'fields' is array containing field definitions
				'pkey' is the primary key name
		"""
		if len(field_defs) == 0:
			return False

		sql = "CREATE TABLE %s (" % self.quoteId(table)
		sql += u", ".join( field_defs )
		if pkey != None and pkey != "":
			sql += u", PRIMARY KEY (%s)" % self.quoteId(pkey)
		sql += ")"

		self._execute_and_commit(sql)
		return True

