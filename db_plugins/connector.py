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

class DBConnector:
	def __init__(self, uri):
		self.connection = None
		self.uri = uri

	def __del__(self):
		print "DBConnector.__del__", self.uri.uri()
		if self.connection != None:
			self.connection.close()
			self.connection = None

	def quoteId(self, identifier):
		if hasattr(identifier, '__iter__'):
			ids = list()
			for i in identifier:
				if i == None:
					continue
				ids.append( self.quoteId(i) )
			return u'.'.join( ids )
			
		identifier = unicode(identifier) # make sure it's python unicode string
		return u'"%s"' % identifier.replace('"', '""')
	
	def quoteString(self, txt):
		""" make the string safe - replace ' with '' """
		txt = unicode(txt) # make sure it's python unicode string
		return u"'%s'" % txt.replace("'", "''")


class SqlTableModel(QAbstractTableModel):
	def __init__(self, parent=None):
		QAbstractTableModel.__init__(self, parent)
		self.header = []
		self.resdata = []
		
	def rowCount(self, parent):
		return len(self.resdata)
	
	def columnCount(self, parent):
		return len(self.header)
	
	def data(self, index, role):
		if role != Qt.DisplayRole:
			return QVariant()
		
		val = self.resdata[ index.row() ][ index.column() ]
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
