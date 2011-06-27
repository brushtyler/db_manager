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

from qgis.gui import QgsMapCanvas

class LayerPreview(QgsMapCanvas):
	def __init__(self, parent=None):
		QgsMapCanvas.__init__(self, parent)
		self.dirtyMap = True
		self.setCanvasColor(QColor(255,255,255))

		# reuse settings from QGIS
		settings = QSettings()
		self.enableAntiAliasing( settings.value( "/qgis/enable_anti_aliasing", QVariant(False) ).toBool() )
		self.useImageToRender( settings.value( "/qgis/use_qimage_to_render", QVariant(False) ).toBool() )
		action = settings.value( "/qgis/wheel_action", QVariant(0) ).toInt()[0]
		zoomFactor = settings.value( "/qgis/zoom_factor", QVariant(2) ).toDouble()[0]
		self.setWheelAction( QgsMapCanvas.WheelAction(action), zoomFactor )


	def load(self, item):
		return
		""" if has geometry column load to map canvas """
		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

		if item and item.geom_type:
			uri = self.db.getURI()

			# if the limit checkbox is checked and there is more than 1000 rows, limit the query result
			if self.tableFilterCheck.isChecked() and self.db.get_table_rows(item.name, item.schema().name) > 1000:
				# retrieve an unique field
				uniqueField = None

				fields = self.db.get_table_fields(item.name, item.schema().name)
				if self.db.getTypeName() == 'postgis':
					tableName = self.db._table_name(item.schema().name, item.name)

					constraints = self.db.get_table_constraints(item.name, item.schema().name)
					uniqueIndexes = self.db.get_table_unique_indexes(item.name, item.schema().name)

					for fld in fields:
						# add both the serial and int4 fields with unique index
						for u in uniqueIndexes:
							if ( fld.data_type == "oid" or fld.data_type == "serial" or fld.data_type == "int4" ) and \
									len(u.columns) == 1 and fld.num in u.columns:
								uniqueField = ( None, fld.name )
								continue

						# add pk and unique fields to the unique combo
						for c in constraints:
							if c.con_type == DbConnection.TableConstraint.TypePrimaryKey and \
									len(c.keys) == 1 and fld.num in c.keys:
								uniqueField = (DbConnection.TableConstraint.TypePrimaryKey, fld.name)
								break

							if c.con_type == DbConnection.TableConstraint.TypeUnique and \
									len(c.keys) == 1 and fld.num in c.keys:
								uniqueField = (DbConnection.TableConstraint.TypeUnique, fld.name)
								break

						if uniqueField[0] == DbConnection.TableConstraint.TypePrimaryKey:
							break

				elif self.db.getTypeName() == 'spatialite':
					tableName = self.db._quote(item.name)

					for fld in fields:
						if fld.primary_key:
							uniqueField = ( DbConnection.TableConstraint.TypePrimaryKey, fld.name )
							break

				if uniqueField == None:
					raise Exception("unique field not found")

				uri.setDataSource("", "(SELECT * FROM %s LIMIT 1000)" % tableName, item.geom_column, "", uniqueField[1])

			else:
				schema = item.schema().name
				uri.setDataSource(schema if schema else '', item.name, item.geom_column)

			vl = qgis.core.QgsVectorLayer(uri.uri(), item.name, self.db.getProviderName())
			if not vl.isValid():
				newLayerId = None
				self.setLayerSet( [] )
			else:
				newLayerId = vl.getLayerID()
				qgis.core.QgsMapLayerRegistry.instance().addMapLayer(vl, False)
				self.setLayerSet( [ qgis.gui.QgsMapCanvasLayer(vl, True, False) ] )
				self.zoomToFullExtent()
				
		else:
			newLayerId = None
			self.setLayerSet( [] )
			
		# remove old layer (if any) and set new
		if self.currentLayerId:
			qgis.core.QgsMapLayerRegistry.instance().removeMapLayer(self.currentLayerId, False)
		self.currentLayerId = newLayerId

		QApplication.restoreOverrideCursor()

		self.dirtyMap = False

	def clear(self):
		""" remove any layers from preview canvas """
		self.setLayerSet( [] )
		self.dirtyMap = False

