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
	return PostGisDBPlugin

class PostGisDBPlugin(DBPlugin):

	@classmethod
	def icon(self):
		return QIcon(":/icons/postgis_elephant.png")

	@classmethod
	def typeName(self):
		return 'postgis'

	@classmethod
	def typeNameString(self):
		return 'PostGIS'

	@classmethod
	def connectionSettingsKey(self):
		return '/PostgreSQL/connections'

	def connect(self, parent=None):
		conn_name = self.connectionName()
		settings = QSettings()
		settings.beginGroup( u"/%s/%s" % (self.connectionSettingsKey(), conn_name) )

		if not settings.contains( "database" ): # non-existent entry?
			raise InvalidDataException( 'there is no defined database connection "%s".' % conn_name )
	
		get_value_str = lambda x: unicode(settings.value(x).toString())
		host, port, database, username, password = map(get_value_str, ["host", "port", "database", "username", "password"])

		# qgis1.5 use 'savePassword' instead of 'save' setting
		if not ( settings.value("save").toBool() or settings.value("savePassword").toBool() ):
			#dlg = qgis.gui.QgsCredentialDialog(parent)
			#(ok, username, password) = dlg.request(selected)
			(password, ok) = QInputDialog.getText(parent, "Enter password", 'Enter password for connection "%s":' % conn_name, QLineEdit.Password)
			if not ok: return False

		settings.endGroup()

		import qgis.core
		from .connector import PostGisDBConnector
		uri = qgis.core.QgsDataSourceURI()
		uri.setConnection(host, port, database, username, password)
		self.connector = PostGisDBConnector(uri)
		return True
