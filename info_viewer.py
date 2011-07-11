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

from .db_plugins.plugin import DbError, DBPlugin, Schema, Table
from .dlg_db_error import DlgDbError

class InfoViewer(QTextBrowser):

	def __init__(self, parent=None):
		QTextBrowser.__init__(self, parent)
		self.setOpenLinks(False)
		self._clear()
		self.connect(self, SIGNAL("anchorClicked(const QUrl&)"), self._linkClicked)

	def _linkClicked(self, url):
		if self.item == None:
			return

		if url.scheme() == "action":
			try:
				if self.item.runAction( url.path() ):
					self.refresh()
			except DbError, e:
				DlgDbError.showError(e, self)

	def refresh(self):
		self.showInfo( self.item, True )		

	def showInfo(self, item, force=False):
		if item == self.item and not force: 
			return
		self._clear()

		self.item = item
		if isinstance(item, DBPlugin):
			self._showDatabaseInfo(item)
		elif isinstance(item, Schema):
			self._showSchemaInfo(item)
		elif isinstance(item, Table):
			self._showTableInfo(item)

	def _clear(self):
		self.item = None
		self.setHtml("")

	def _showDatabaseInfo(self, connection):
		html  = u'<div style="background-color:#ccffcc;"><h1>&nbsp;%s</h1></div>' % connection.connectionName()
		html += '<div style="margin-left:8px;">'
		if connection.database() == None:
			html += connection.info().toHtml()
		else:
			html += connection.database().info().toHtml()			
		html += '</div>'
		self.setHtml(html)
	
	
	def _showSchemaInfo(self, schema):
		html  = u'<div style="background-color:#ffcccc;"><h1>&nbsp;%s</h1></div>' % schema.name
		html += '<div style="margin-left:8px;">'
		html += schema.info().toHtml()
		html += "</div>"
		self.setHtml(html)


	def _showTableInfo(self, table):		
		html = '<div style="background-color:#ccccff"><h1>&nbsp;%s</h1></div>' % table.name
		html += '<div style="margin-left:8px;">'
		html += table.info().toHtml()
		html += '</div>'
		self.setHtml(html)
		return True



	def setHtml(self, html):
		# convert special tags :)
		html = unicode(html).replace( '<warning>', '<img src=":/db_manager/warning">&nbsp;&nbsp; ' )

		# add default style
		html = u"""
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<style type="text/css">
	.section { margin-top: 25px; }
	table.header th { background-color: #dddddd; }
	table.header td { background-color: #f5f5f5; }
	table.header th, table.header td { padding: 0px 10px; }
	table td { padding-right: 20px; }
	.underline { text-decoration:underline; }
</style>
</head>
<body>
%s <br>
</body>
</html>
""" % html

		#print ">>>>>\n", html, "\n<<<<<<"
		return QTextBrowser.setHtml(self, html)

