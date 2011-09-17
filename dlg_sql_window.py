# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name                 : DB Manager
Description          : Database manager plugin for QuantumGIS
Date                 : May 23, 2011
copyright            : (C) 2011 by Giuseppe Sucameli
email                : brush.tyler@gmail.com

The content of this file is based on 
PostGIS Manager by Martin Dobias
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

from .ui.DlgSqlWindow_ui import Ui_DlgSqlWindow

from .db_plugins.plugin import DbError
from .dlg_db_error import DlgDbError

from highlighter import SqlHighlighter

class DlgSqlWindow(QDialog, Ui_DlgSqlWindow):

	def __init__(self, iface, db, parent=None):
		QDialog.__init__(self, parent)
		self.iface = iface
		self.db = db
		self.setupUi(self)

		self.defaultLayerName = 'QueryLayer'

		settings = QSettings()
		self.restoreGeometry(settings.value("/DB_Manager/sqlWindow/geometry").toByteArray())

		self.editSql.setAcceptRichText(False)
		SqlHighlighter(self.editSql).load(self.db)
		
		self.connect(self.btnExecute, SIGNAL("clicked()"), self.executeSql)
		self.connect(self.btnClear, SIGNAL("clicked()"), self.clearSql)
		self.connect(self.buttonBox.button(QDialogButtonBox.Close), SIGNAL("clicked()"), self.close)

		# hide the load query as layer if feature is not supported
		self._loadAsLayerAvailable = self.db.connector.hasCustomQuerySupport()
		self.loadAsLayerGroup.setVisible( self._loadAsLayerAvailable )
		if self._loadAsLayerAvailable:
			self.layerTypeWidget.hide()	# show if load as raster is supported
			self.connect(self.loadLayerBtn, SIGNAL("clicked()"), self.loadSqlLayer)
			self.connect(self.getColumnsBtn, SIGNAL("clicked()"), self.fillColumnCombos)
			self.connect(self.loadAsLayerGroup, SIGNAL("toggled(bool)"), self.loadAsLayerToggled)
			self.loadAsLayerToggled(False)


	def closeEvent(self, e):
		""" save window state """
		settings = QSettings()
		settings.setValue("/DB_Manager/sqlWindow/geometry", QVariant(self.saveGeometry()))
		
		QDialog.closeEvent(self, e)

	def loadAsLayerToggled(self, checked):
		self.loadAsLayerGroup.setChecked( checked )
		self.loadAsLayerWidget.setVisible( checked )

		
	def clearSql(self):
		self.editSql.setPlainText(QString())

	def executeSql(self):
		sql = self.editSql.toPlainText()
		if sql.isEmpty():
			return

		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

		# delete the old model 
		old_model = self.viewResult.model()
		self.viewResult.setModel(None)
		if old_model: old_model.deleteLater()

		self.uniqueCombo.clear()
		self.geomCombo.clear()

		try:
			# set the new model 
			model = self.db.sqlDataModel( sql, self )
			self.viewResult.setModel( model )
			self.lblResult.setText("%d rows, %.1f seconds" % (model.rowCount(), model.secs()))

		except DbError, e:
			QApplication.restoreOverrideCursor()
			DlgDbError.showError(e, self)
			return

		cols = self.viewResult.model().columnNames()
		cols.sort()
		self.uniqueCombo.addItems( cols )
		self.geomCombo.addItems( cols )

		self.update()
		QApplication.restoreOverrideCursor()


	def loadSqlLayer(self):
		uniqueFieldName = self.uniqueCombo.currentText()
		geomFieldName = self.geomCombo.currentText()

		if geomFieldName.isEmpty() or uniqueFieldName.isEmpty():
			QMessageBox.warning(self, self.tr( "Sorry" ), self.tr( "You must fill the required fields: \ngeometry column - column with unique integer values" ) )
			return

		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

		query = self.editSql.toPlainText()
		from qgis.core import QgsMapLayer, QgsMapLayerRegistry
		layerType = QgsMapLayer.VectorLayer if self.vectorRadio.isChecked() else QgsMapLayer.RasterLayer

		# get a new layer name
		names = []
		for layer in QgsMapLayerRegistry.instance().mapLayers().values():
			names.append( layer.name() )

		layerName = self.layerNameEdit.text()
		if layerName.isEmpty():
			layerName = self.defaultLayerName
		newLayerName = layerName
		index = 1
		while newLayerName in names:
			index += 1
			newLayerName = u"%s_%d" % (layerName, index)

		# create the layer
		layer = self.db.toSqlLayer(query, geomFieldName, uniqueFieldName, newLayerName, layerType)
		if layer.isValid():
			QgsMapLayerRegistry.instance().addMapLayer(layer, True)

		QApplication.restoreOverrideCursor()

	def fillColumnCombos(self):
		query = self.editSql.toPlainText()
		if query.isEmpty():
			return

		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
		self.uniqueCombo.clear()
		self.geomCombo.clear()

		# get a new alias
		aliasIndex = 0
		while True:
			alias = "_%s__%d" % ("subQuery", aliasIndex)
			escaped = '\\b("?)' + QRegExp.escape(alias) + '\\1\\b' 
			if not query.contains( QRegExp(escaped, Qt.CaseInsensitive) ):
				break
			aliasIndex += 1

		# get all the columns
		cols = []
		connector = self.db.connector
		sql = u"SELECT * FROM (%s\n) AS %s LIMIT 0" % ( unicode(query), connector.quoteId(alias) )
		c = connector._get_cursor()

		try:
			connector._execute(c, sql)
			cols = connector._get_columns(c)

		except DbError, e:
			QApplication.restoreOverrideCursor()
			DlgDbError.showError(e, self)
			return

		finally:
			c.close()
			del c

		cols.sort()
		self.uniqueCombo.addItems( cols )
		self.geomCombo.addItems( cols )

		QApplication.restoreOverrideCursor()

