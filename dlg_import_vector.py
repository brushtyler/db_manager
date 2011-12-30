# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name                 : DB Manager
Description          : Database manager plugin for QuantumGIS
Date                 : Oct 13, 2011
copyright            : (C) 2011 by Giuseppe Sucameli
email                : brush.tyler@gmail.com

The content of this file is based on 
- PG_Manager by Martin Dobias (GPLv2 license)
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

import qgis.core

from .db_plugins.plugin import DbError
from .dlg_db_error import DlgDbError

from ui.DlgImportVector_ui import Ui_DlgImportVector

class DlgImportVector(QDialog, Ui_DlgImportVector):

	def __init__(self, inLayer, outDb, outUri, parent=None):
		QDialog.__init__(self, parent)
		self.inLayer = inLayer
		self.db = outDb
		self.outUri = outUri
		self.setupUi(self)
		
		# updates of UI
		for widget in [self.radCreate, self.chkDropTable, self.radAppend, 
						self.chkPrimaryKey, self.chkGeomColumn, self.chkSpatialIndex, 
						self.chkSourceSrid, self.chkTargetSrid, self.chkEncoding]:
			self.connect(widget, SIGNAL("clicked()"), self.updateUi)

		self.connect(self.cboSchema, SIGNAL("currentIndexChanged(int)"), self.populateTables)
		self.connect(self.buttonBox, SIGNAL("accepted()"), self.importLayer)
		
		self.populateSchemas()
		self.populateTables()
		self.populateEncodings()
		self.updateUi()

		self.cboTable.setEditText(self.outUri.table())
		pk = self.outUri.keyColumn()
		self.editPrimaryKey.setText(pk if pk != "" else "pk")
		geom = self.outUri.geometryColumn()
		self.editGeomColumn.setText(geom if geom != "" else "geom")
		inCrs = self.inLayer.crs()
		srid = inCrs.postgisSrid() if inCrs.isValid() else 4236
		self.editSourceSrid.setText( "%s" % srid )
		self.editTargetSrid.setText( "%s" % srid )

		self.checkSupports()


	def checkSupports(self):
		allowSpatial = self.db.connector.hasSpatialSupport()
		self.chkGeomColumn.setEnabled(allowSpatial)
		self.chkSourceSrid.setEnabled(allowSpatial)
		self.chkTargetSrid.setEnabled(allowSpatial)
		self.chkSpatialIndex.setEnabled(allowSpatial)
	
		
	def populateSchemas(self):
		if not self.db:
			return
		
		self.cboSchema.clear()
		schemas = self.db.schemas()
		if schemas == None:
			self.hideSchemas()
			return

		index = -1
		for schema in schemas:
			self.cboSchema.addItem(schema.name)
			if schema.name == self.outUri.schema():
				index = self.cboSchema.count()-1
		self.cboSchema.setCurrentIndex(index)

	def hideSchemas(self):
		self.cboSchema.setEnabled(False)

	def populateTables(self):
		if not self.db:
			return
		
		currentText = self.cboTable.currentText()

		schemas = self.db.schemas()
		if schemas != None:
			schema_name = self.cboSchema.currentText()
			matching_schemas = filter(lambda x: x.name == schema_name, schemas)
			tables = matching_schemas[0].tables() if len(matching_schemas) > 0 else []
		else:
			tables = self.db.tables()

		self.cboTable.clear()
		for table in tables:
			self.cboTable.addItem(table.name)

		self.cboTable.setEditText(currentText)
	
	def populateEncodings(self):
		encodings = ['ISO-8859-1', 'ISO-8859-2', 'UTF-8', 'CP1250']
		for enc in encodings:
			self.cboEncoding.addItem(enc)
		self.cboEncoding.setCurrentIndex(2)

	def updateUi(self):
		allowDropTable = self.radCreate.isChecked()
		self.chkDropTable.setEnabled(allowDropTable)
		
		allowSetPrimaryKey = self.chkPrimaryKey.isChecked()
		self.editPrimaryKey.setEnabled(allowSetPrimaryKey)

		allowSetGeomColumn = self.chkGeomColumn.isChecked()
		self.editGeomColumn.setEnabled(allowSetGeomColumn)

		allowSetSourceSrid = self.chkSourceSrid.isChecked()
		self.editSourceSrid.setEnabled(allowSetSourceSrid)

		allowSetTargetSrid = self.chkTargetSrid.isChecked()
		self.editTargetSrid.setEnabled(allowSetTargetSrid)
		
		allowSetEncoding = self.chkEncoding.isChecked()
		self.cboEncoding.setEnabled(allowSetEncoding)

		
	def importLayer(self):
		# sanity checks
		if self.cboTable.currentText().isEmpty():
			QMessageBox.information(self, "error", "Table name is empty!")
			return

		if self.chkSourceSrid.isChecked():
			sourceSrid, ok = self.editSourceSrid.text().toInt()
			if not ok:
				QMessageBox.information(self, "error", "Invalid source srid: must be and integer")
				return

		if self.chkTargetSrid.isChecked():
			targetSrid, ok = self.editTargetSrid.text().toInt()
			if not ok:
				QMessageBox.information(self, "error", "Invalid target srid: must be and integer")
				return

		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

		schema = self.outUri.schema() if not self.cboSchema.isEnabled() else self.cboSchema.currentText()
		table = self.cboTable.currentText()
		pk = self.outUri.keyColumn() if not self.chkPrimaryKey.isChecked() else self.editPrimaryKey.text()
		geom = self.outUri.geometryColumn() if not self.chkGeomColumn.isChecked() else self.editGeomColumn.text()
		sql = self.outUri.sql()
		self.outUri.setDataSource( schema, table, geom, sql, pk )
		uri = self.outUri.uri()

		providerName = self.db.dbplugin().providerName()

		if self.chkSourceSrid.isChecked():
			sourceSrid = self.editSourceSrid.text().toInt()[0]
			inCrs = qgis.core.QgsCoordinateReferenceSystem(sourceSrid)
			self.inLayer.setCrs( inCrs )

		outCrs = None
		if self.chkTargetSrid.isChecked():
			targetSrid = self.editTargetSrid.text().toInt()[0]
			outCrs = qgis.core.QgsCoordinateReferenceSystem(targetSrid)

		if self.chkEncoding.isChecked():
			enc = self.editEncoding.currentText()
			self.inLayer.setProviderEncoding( enc )

		ret, errMsg = qgis.core.QgsVectorLayerImport.importLayer( self.inLayer, uri, providerName, outCrs )
		QApplication.restoreOverrideCursor()
		if ret != 0:
			QMessageBox.warning(self, "Error [%d]" % ret, errMsg )
			return self.reject()

		if self.chkGeomColumn.isChecked() and self.chkSpatialIndex.isChecked():
			self.db.connector.createSpatialIndex( (schema, table), geom )

		QMessageBox.information(self, "Good", "Everything went fine")
		return self.accept()


if __name__ == '__main__':
	import sys
	a = QApplication(sys.argv)
	dlg = DlgLoadData()
	dlg.show()
	sys.exit(a.exec_())
