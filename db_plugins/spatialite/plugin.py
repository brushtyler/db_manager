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

from ...db_plugins import *
try:
	from . import resources_rc
except ImportError:
	pass


def classFactory():
	return SpatiaLiteDBPlugin

class SpatiaLiteDBPlugin(DBPlugin):

	@classmethod
	def icon(self):
		return QIcon(":/icons/spatialite_icon.png")

	@classmethod
	def typeName(self):
		return 'spatialite'

	@classmethod
	def typeNameString(self):
		return 'SpatiaLite'

	@classmethod
	def connectionSettingsKey(self):
		return '/SpatiaLite/connections'


	def connect(self, parent=None):
		conn_name = self.connectionName()
		settings = QSettings()
		settings.beginGroup( u"/%s/%s" % (self.connectionSettingsKey(), conn_name) )

		if not settings.contains( "sqlitepath" ): # non-existent entry?
			raise InvalidDataException( 'there is no defined database connection "%s".' % conn_name )

		database = unicode(settings.value("sqlitepath").toString())

		import qgis.core
		from .connector import SpatiaLiteDBConnector
		uri = qgis.core.QgsDataSourceURI()
		uri.setDatabase(database)
		self.connector = SpatiaLiteDBConnector(uri)
		return True

