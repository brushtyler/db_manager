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

from .db_plugins.plugin import DBPlugin, Schema, Table

class InfoViewer(QTextBrowser):

	def __init__(self, parent=None):
		QTextBrowser.__init__(self, parent)
		self.connect(self, SIGNAL("anchorClicked(const QUrl&)"), self.__linkClicked)
		self.__clear()

	def __del__(self):
		print "InfoViewer.__del__"
		self.item = None

	def __linkClicked(self, url):
		if self.item == None:
			return

		if url.scheme() == "action":
			self.item.runAction( url.path() )
		self.refresh()

	def refresh(self):
		return self.showInfo( self.item )		

	def showInfo(self, item):
		self.item = item
		if isinstance(item, DBPlugin):
			return self.__showDatabaseInfo(item)
		elif isinstance(item, Schema):
			return self.__showSchemaInfo(item)
		elif isinstance(item, Table):
			return self.__showTableInfo(item)
		return self.__clear()

	def __clear(self):
		self.item = None
		self.setHtml("")

	def __showDatabaseInfo(self, connection):
		html  = u'<div style="background-color:#ccffcc;"><h1>&nbsp;%s</h1></div>' % connection.connectionName()
		html += '<div style="margin-left:8px;">'

		db = connection.database()
		if db == None:
			html += '<h2>Not connected</h2>'
			self.setHtml(html)
			return
		
		conn_details = db.connectionDetails()
		if conn_details == None or len(conn_details) <= 0:
			pass
		else:
			html += '<h2>Connection details</h2>'
			html += '<div>'
			html += self.__convert2Html( conn_details )
			html += '</div>'

		general_info = db.generalInfo()
		if general_info == None or len(general_info) <= 0:
			pass
		else:
			html += '<h2>General info</h2>'
			html += '<div>'
			html += self.__convert2Html( general_info )
			html += '</div>'
		
		spatial_info = db.spatialInfo()
		if spatial_info == None:
			pass
		else:
			html += u'<h2>%s</h2>' % connection.typeNameString()
			html += '<div>'
			if len(spatial_info) <= 0:
				html += '<warning>%s support not enabled!' % connection.typeNameString()
			else:
				html += self.__convert2Html( spatial_info )
			html += '</div>'

		priv_details = db.privilegesDetails()
		if priv_details == None:
			pass
		else:
			html += '<h2>Privileges</h2>'
			html += '<div>'
			if len(priv_details) <= 0:
				html += '<warning>This user has no privileges!'
			else:
				html += "User has privileges:<ul>"
				for row in priv_details:
					html += u'<li>%s' % (row)
				html += "</ul>"
			html += "</div>"
				
		self.setHtml(html)
	
	
	def __showSchemaInfo(self, schema):
		html  = u'<div style="background-color:#ffcccc;"><h1>&nbsp;%s</h1></div>' % schema.name
		html += '<div style="margin-left:8px;">'

		general_info = schema.generalInfo()
		if general_info == None or len(general_info) <= 0:
			pass
		else:
			html += '<h2>Schema details</h2>'
			html += '<div>'
			html += self.__convert2Html( general_info )
			html += '</div>'

		priv_details = schema.privilegesDetails()
		if priv_details == None:
			pass
		else:
			html += '<h2>Privileges</h2>'
			html += '<div>'
			if len(priv_details) <= 0:
				html += '<warning>This user has no privileges to access this schema!'
			else:
				html += "User has privileges:<ul>"
				for row in priv_details:
					html += u'<li>%s' % (row)
				html += "</ul>"
			html += "</div>"

		self.setHtml(html)


	def __showTableInfo(self, table):		
		html = '<div style="background-color:#ccccff"><h1>&nbsp;%s</h1></div>' % table.name
		html += '<div style="margin-left:8px;">'

		general_info = table.generalInfo()
		if general_info == None or len(general_info) <= 0:
			pass
		else:
			html += '<h2>General info</h2>'
			html += '<div>'
			html += self.__convert2Html( general_info )
			html += '</div>'
			

		if False:
			# permissions
			priv_details = table.privilegesDetails()
			if priv_details ==  None:
				pass
			else:
				html += '<h2>Privileges</h2>'
				html += '<div>'

				# has the user access to this schema?
				schema_priv = table.schema().privilegesDetails() if table.schema() else None
				if schema_priv == None:
					pass
				else:
					if len(schema_priv) <= 0:
						html += '<div><warning>This user doesn\'t have usage privileges for this schema!</div>'

				if len(priv_details) <= 0:
					html += '<warning>This user has no privileges!'
				else:
					html += "User has privileges:"
					html += '<ul>'
					for row in priv_details:
						html += u"<li>%s" % (row)
					html += "</ul>"
				html += "</div>"

		# spatial info
		spatial_info = table.spatialInfo()
		if spatial_info == None:
			pass
		else:
			html += u'<h2>%s</h2>' % table.database().connection().typeNameString()
			html += '<div>'
			if len(spatial_info) <= 0:
				html += u'<warning>This is not a spatial table.'
			else:
				html += self.__convert2Html( spatial_info )
			html += '</div>'

		# fields
		fields_details = table.fieldsDetails()
		if fields_details == None:
			pass
		else:
			if len(fields_details) <= 0:
				pass
			html += '<h2>Fields</h2>'
			html += '<div>'
			html += self.__convert2Html( fields_details )
			html += '</div>'

		self.setHtml(html)
		return		


		html += '<table><tr bgcolor="#dddddd">'
		html += '<th width="30"># <th width="180">Name <th width="100">Type '
		if self.db.getTypeName() == 'postgis':
			html += '<th width="50">Length'
		html += '<th width="50">Null <th>Default '
		for fld in fields:
			is_null_txt = "N" if fld.notnull else "Y"
			default = fld.default if fld.hasdefault else ""
			if not hasattr(fld, 'modifier') or fld.modifier == -1:
				fldtype = fld.data_type
			else: fldtype = "%s (%d)" % (fld.data_type, fld.modifier)
			
			# find out whether it's part of primary key
			pk_style = ''
			if self.db.getTypeName() == 'postgis':
				for con in constraints:
					if con.con_type == DbConnection.TableConstraint.TypePrimaryKey and fld.num in con.keys:
						pk_style = ' style="text-decoration:underline;"'
						break

			elif self.db.getTypeName() == 'spatialite':
				if fld.primary_key:
					pk_style = ' style="text-decoration:underline;"'

			html += '<tr><td align="center">%s<td%s>%s<td>%s' % (fld.num, pk_style, fld.name, fldtype)
			if self.db.getTypeName() == 'postgis':
				html += '<td align="center">%d' % fld.char_max_len
			html += '<td align="center">%s<td>%s' % (is_null_txt, default)
		html += "&nbsp;</table></div> "


		# constraints
		constraints_details = table.constraintsDetails()
		if constraints_details ==  None or len(constraints_details) <= 0:
			pass
		else:
			html += '<h2>Constraints</h2>'
			html += '<div>'
			html += self.__convert2Html( constraints_details )
			html += '</div>'

		if self.db.getTypeName() == 'postgis':
			if len(constraints) != 0:
				html += '<div style=" margin-top:30px;><h2>Constraints</h2>'
				html += '<table><tr bgcolor="#dddddd"><th width="180">Name<th width="100">Type<th width="180">Column(s)'
				for con in constraints:
					if   con.con_type == DbConnection.TableConstraint.TypeCheck:      con_type = "Check"
					elif con.con_type == DbConnection.TableConstraint.TypePrimaryKey: con_type = "Primary key"
					elif con.con_type == DbConnection.TableConstraint.TypeForeignKey: con_type = "Foreign key"
					elif con.con_type == DbConnection.TableConstraint.TypeUnique:     con_type = "Unique"
					keys = ""
					for key in con.keys:
						if len(keys) != 0: keys += "<br>"
						keys += self._field_name_by_number(key, fields)
					html += "<tr><td>%s<td>%s<td>%s" % (con.name, con_type, keys)
				html += "&nbsp;</table></div>"


		# indexes
		indexes_details = table.indexesDetails()
		if indexes_details ==  None or len(indexes_details) <= 0:
			pass
		else:
			html += '<h2>Indexes</h2>'
			html += '<div>'
			html += self.__convert2Html( indexes_details )
			html += '</div>'

		if len(indexes) != 0:
			html += '<div style=" margin-top:30px;"><h2>Indexes</h2>'
			html += '<table><tr bgcolor="#dddddd"><th width="180">Name<th width="180">Column(s)'
			for fld in indexes:
				keys = ""
				for key in fld.columns:
					if len(keys) != 0: keys += "<br>"
					keys += self._field_name_by_number(key, fields)
				html += "<tr><td>%s<td>%s" % (fld.name, keys)
			html += "&nbsp;</table></div>"


		# triggers
		triggers_details = table.indexesDetails()
		if triggers_details ==  None or len(triggers_details) <= 0:
			pass
		else:
			html += '<h2>Triggers</h2>'
			html += '<div>'
			html += self.__convert2Html( triggers_info )
			html += '</div>'

		if len(triggers) != 0:
			html += '<div style=" margin-top:30px;"><h2>Triggers</h2>'
			html += '<table><tr bgcolor="#dddddd"><th width="180">Name<th>Function'
			if self.db.getTypeName() == 'postgis':
				html += '<th>Type<th>Enabled'

			for trig in triggers:
				if self.db.getTypeName() == 'postgis':
					trig_type = "Before " if trig.type & DbConnection.TableTrigger.TypeBefore else "After "
					if trig.type & DbConnection.TableTrigger.TypeInsert: trig_type += "INSERT "
					if trig.type & DbConnection.TableTrigger.TypeUpdate: trig_type += "UPDATE "
					if trig.type & DbConnection.TableTrigger.TypeDelete: trig_type += "DELETE "
					if trig.type & DbConnection.TableTrigger.TypeTruncate: trig_type += "TRUNCATE "
					trig_type += "<br>for each "
					trig_type += "row" if trig.type & DbConnection.TableTrigger.TypeRow else "statement"
					if trig.enabled:
						txt_enabled = 'Yes (<a href="action:trigger/%s/disable">disable</a>)' % trig.name
					else:
						txt_enabled = 'No (<a href="action:trigger/%s/enable">enable</a>)' % trig.name
					html += '<tr><td>%s (<a href="action:trigger/%s/delete">delete</a>)<td>%s<td>%s<td>%s' % (trig.name, trig.name, trig.function, trig_type, txt_enabled)

				elif self.db.getTypeName() == 'spatialite':
					html += '<tr><td>%s<td>%s' % (trig.name, trig.function)

			html += "&nbsp;</table>"
			if self.db.getTypeName() == 'postgis':
				html += "<a href=\"action:triggers/enable\">Enable all triggers</a> / <a href=\"action:triggers/disable\">Disable all triggers</a>"
			html += "</div>"


		# rules
		rules_details = table.rulesDetails()
		if rules_details ==  None or len(rules_details) <= 0:
			pass
		else:
			html += '<div style=" margin-top:30px;">'
			html += '<h2>Rules</h2>'
			html += '<div>'
			html += self.__convert2Html( rules_info )
			html += '</div>'

			html += '<table><tr bgcolor="#dddddd"><th width="180">Name<th>Definition'
			for rule in rules:
				html += '<tr><td>%s (<a href="action:rule/%s/delete">delete</a>)<td>%s' % (rule.name, rule.name, rule.definition)
			html += "&nbsp;</table></div>"
	

		if table.isView:
			html += '<div style=" margin-top:30px;">'
			html += '<h2>View definition</h2>'
			html += '<p>%s</p>' % table.getViewDefinition()
			html += '</div>'
		

		self.setHtml(html)
		#return priv[0] # ability to SELECT?
		return True



	def setHtml(self, html):
		html = unicode(html).replace( '<warning>', '<img src=":/icons/warning-20px.png">&nbsp;&nbsp; ' )
		html = unicode(html).replace( '<warning>', '<img src=":/icons/warning-20px.png">&nbsp;&nbsp; ' )
		html = u"""
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<style type="text/css">
table.header tr { background-color: #dddddd; }
</style>
</head>
<body> %s </body>
</html>
""" % html
		#print ">>>>>\n", html, "\n<<<<<<"
		return QTextBrowser.setHtml(self, html)


	def _field_name_by_number(self, num, fields):
		""" return field specified by its number or None if doesn't exist """
		for fld in fields:
			if fld.num == num:
				return fld.name
		return "??? (#%d)" % num


	def __convertTxt2Html(self, t):
		return u"%s" % unicode(t).replace("\n", "<br>")

	def __convertTable2Html(self, t):
		if self.__isString(t) or self.__isNumber(t):
			t = [t]

		rows = []
		maxcols = 0
		props = {}
		for i, row in enumerate(t):
			if i == 0 and isinstance(row, dict):
				props = row
			else:
				rows.append( row )
				maxcols = max(maxcols, len(row))

		html = u''
		if maxcols == 1:
			for row in rows:
				html += u'<p class="%s">' % props['p.class'] if props.has_key('p.class') else '<p>'
				html += u'%s</p>' % self.__convertTxt2Html(row)

		else:
			html += u'<table class="%s">' % props['table.class'] if props.has_key('table.class') else '<table>'
			for row in rows:
				if self.__isString(row) or self.__isNumber(row):
					row = [row]

				html += u'<tr class="%s">' % props['tr.class'] if props.has_key('tr.class') else '<tr>'
				for i, col in enumerate(row):
					if i >= maxcols:
						break
					elif len(row) > 1 and i == 0:
						html += u'<td width="150"'
					elif i >= len(row)-1 and i < maxcols-1:
						html += u'<td colspan="%d"' % (maxcols-len(row))
					else:
						html += u'<td'
					html += u' class="%s">' % props['td.class'] if props.has_key('td.class') else '>'
					html += u'%s' % self.__convertTxt2Html(col)

			html += '</table>'
		return html

	def __convert2Html(self, t):
		if self.__isString(t) or self.__isNumber(t):
			return self.__convertTxt2Html(t)
		return self.__convertTable2Html(t)


	def __isString(self, t):
		return isinstance(t, str) or isinstance(t, unicode) or isinstance(t, QString)

	def __isNumber(self, t):
		return isinstance(t, int) or isinstance(t, float) or isinstance(t, bool)

