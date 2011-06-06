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

class NotSupportedDBType(Exception):
	def __init__(self, dbtype):
		self.msg = u"%s is not supported yet" % dbtype
		Exception(self, self.msg)

	def __str__(self):
		return self.msg.encode('utf-8')

class InvalidDataException(Exception):
	def __init__(self, msg):
		self.msg = unicode( msg )
		Exception(self, self.msg)

	def __str__(self):
		return self.msg.encode('utf-8')

class DbError(Exception):
	def __init__(self, errormsg, query=None):
		self.msg = unicode( errormsg )
		self.query = unicode( query ) if query else None
		Exception(self, self.msg)

	def __str__(self):
		msg = self.msg
		if self.query != None:
			msg += u"\nQuery:\n%s" % self.query
		return msg.encode('utf-8')


class DBConnector:
	def __init__(self, uri):
		self.uri = uri

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
		return txt.replace("'", "''")



class DBPlugin:
	def __init__(self, conn_name):
		self.connName = conn_name

	def connectionName(self):
		return self.connName

	def connect(self):
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
			conn_list.append( create(self.typeName(), name) )
		settings.endGroup()
		return conn_list


def init():
	import os
	current_dir = os.path.dirname(__file__)
	for name in os.listdir(current_dir):
		if not os.path.isdir( os.path.join( current_dir, name ) ):
			continue
		try:
			exec( u"from %s import plugin as mod" % name  )
		except :
			continue
		plugin_class = mod.classFactory()
		SUPPORTED_DBTYPES[ plugin_class.typeName() ] = plugin_class
	return len(SUPPORTED_DBTYPES) > 0

def supportedDBTypes():
	return sorted(SUPPORTED_DBTYPES.keys())

def create(dbtype, conn_name=None):
	if not SUPPORTED_DBTYPES.has_key( dbtype ):
		raise NotSupportedDBType( dbtype )
	dbplugin = SUPPORTED_DBTYPES[ dbtype ]
	return dbplugin if conn_name is None else dbplugin(conn_name)


# initialize the plugin list
SUPPORTED_DBTYPES = {}
init()
