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
		self._uri = uri

	def __del__(self):
		pass	#print "DBConnector.__del__", self._uri.connectionInfo()
		if self.connection != None: 
			self.connection.close()
		self.connection = None

	def uri(self):
		import qgis.core
		return qgis.core.QgsDataSourceURI( self._uri.uri() )

	def hasCustomQuerySupport(self):
		return False

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

