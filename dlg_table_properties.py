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

from .db_plugins.data_model import TableFieldsModel, TableConstraintsModel, TableIndexesModel
from .db_plugins.plugin import DbError
from .dlg_db_error import DlgDbError

from dlg_field_properties import DlgFieldProperties
from dlg_add_geometry_column import DlgAddGeometryColumn
from dlg_create_constraint import DlgCreateConstraint
from dlg_create_index import DlgCreateIndex

from ui.DlgTableProperties_ui import Ui_DlgTableProperties

class DlgTableProperties(QDialog, Ui_DlgTableProperties):
	
	def __init__(self, table, parent=None):
		QDialog.__init__(self, parent)
		self.table = table
		self.setupUi(self)
		
		self.db = self.table.database()
		
		m = TableFieldsModel(self)
		self.viewFields.setModel(m)
		self.populateFields()
		
		m = TableConstraintsModel(self)
		self.viewConstraints.setModel(m)
		self.populateConstraints()
		
		m = TableIndexesModel(self)
		self.viewIndexes.setModel(m)
		self.populateIndexes()
		
		self.connect(self.btnAddColumn, SIGNAL("clicked()"), self.addColumn)
		self.connect(self.btnAddGeometryColumn, SIGNAL("clicked()"), self.addGeometryColumn)
		self.connect(self.btnEditColumn, SIGNAL("clicked()"), self.editColumn)
		self.connect(self.btnDeleteColumn, SIGNAL("clicked()"), self.deleteColumn)
		
		self.connect(self.btnAddConstraint, SIGNAL("clicked()"), self.addConstraint)
		self.connect(self.btnDeleteConstraint, SIGNAL("clicked()"), self.deleteConstraint)
		
		self.connect(self.btnAddIndex, SIGNAL("clicked()"), self.createIndex)
		self.connect(self.btnAddSpatialIndex, SIGNAL("clicked()"), self.createSpatialIndex)
		self.connect(self.btnDeleteIndex, SIGNAL("clicked()"), self.deleteIndex)
		

	def refresh(self):
		self.populateFields()
		self.populateConstraints()
		self.populateIndexes()


	def populateFields(self):
		""" load field information from database """
		
		m = self.viewFields.model()
		m.clear()

		for fld in self.table.fields():
			m.append( fld )
		
		for col in range(4):
			self.viewFields.resizeColumnToContents(col)

	def currentColumn(self):
		""" returns row index of selected column """
		sel = self.viewFields.selectionModel()
		indexes = sel.selectedRows()
		if len(indexes) == 0:
			QMessageBox.information(self, "sorry", "nothing selected")
			return -1
		return indexes[0].row()

	def addColumn(self):
		""" open dialog to set column info and add column to table """
		dlg = DlgFieldProperties(self, None, self.table)
		if not dlg.exec_():
			return
		fld = dlg.getField()
		
		QApplication.setOverrideCursor(Qt.WaitCursor)
		self.emit(SIGNAL("aboutToChangeTable()"))
		try:
			# add column to table
			self.table.addField(fld)
			self.refresh()
		except DbError, e:
			DlgDbError.showError(e, self)
			return
		finally:
			QApplication.restoreOverrideCursor()

	def addGeometryColumn(self):
		""" open dialog to add geometry column """
		dlg = DlgAddGeometryColumn(self, self.table)
		if not dlg.exec_():
			return
		self.refresh()

	def editColumn(self):
		""" open dialog to change column info and alter table appropriately """
		index = self.currentColumn()
		if index == -1:
			return
		
		m = self.viewFields.model()
		# get column in table
		# (there can be missing number if someone deleted a column)
		fld = m.getObject(index)

		dlg = DlgFieldProperties(self, fld, self.table)
		if not dlg.exec_():
			return
		new_fld = dlg.getField(True)
		
		QApplication.setOverrideCursor(Qt.WaitCursor)
		self.emit(SIGNAL("aboutToChangeTable()"))
		try:
			if fld.name != new_fld.name:
				fld.rename(new_fld.name)
			if fld.dataType != new_fld.dataType or fld.modifier != new_fld.modifier:
				fld.setType(new_fld.name, new_fld.type2String())
			if fld.notNull != new_fld.notNull:
				fld.setNull(new_fld.name, not new_fld.notNull)
			if fld.default != new_fld.default:
				fld.setDefault(new_fld.name, new_fld.default)
			
			self.refresh()
		except DbError, e:
			DlgDbError.showError(e, self)
			return
		finally:
			QApplication.restoreOverrideCursor()

	def deleteColumn(self):
		""" delete currently selected column """
		index = self.currentColumn()
		if index == -1:
			return
		
		m = self.viewFields.model()
		fld = m.getObject(index)
		
		res = QMessageBox.question(self, "are you sure", u"really delete column '%s' ?" % fld.name, QMessageBox.Yes | QMessageBox.No)
		if res != QMessageBox.Yes:
			return
		
		QApplication.setOverrideCursor(Qt.WaitCursor)
		self.emit(SIGNAL("aboutToChangeTable()"))
		try:
			fld.delete()
			self.refresh()
		except DbError, e:
			DlgDbError.showError(e, self)
			return
		finally:
			QApplication.restoreOverrideCursor()

	
	def populateConstraints(self):
		constraints = self.table.constraints()
		if constraints == None:
			self.hideConstraints()	# not supported
			return

		m = self.viewConstraints.model()
		m.clear()
		
		for constr in constraints:
			m.append( constr )

		for col in range(3):
			self.viewConstraints.resizeColumnToContents(col)

	def hideConstraints(self):
		index = self.tabs.indexOf(self.tabConstraints)
		if index >= 0:
			self.tabs.setTabEnabled(index, False)

	def addConstraint(self):
		""" add primary key or unique constraint """
		
		dlg = DlgCreateConstraint(self, self.table)
		if not dlg.exec_():
			return
		self.refresh()

	def deleteConstraint(self):
		""" delete a constraint """
		
		index = self.currentConstraint()
		if index == -1:
			return

		m = self.viewConstraints.model()
		constr = m.getObject(index)

		res = QMessageBox.question(self, "are you sure", u"really delete constraint '%s' ?" % constr.name, QMessageBox.Yes | QMessageBox.No)
		if res != QMessageBox.Yes:
			return
		
		QApplication.setOverrideCursor(Qt.WaitCursor)
		self.emit(SIGNAL("aboutToChangeTable()"))
		try:
			constr.delete()
			self.refresh()
		except DbError, e:
			DlgDbError.showError(e, self)
			return
		finally:
			QApplication.restoreOverrideCursor()

	def currentConstraint(self):
		""" returns row index of selected index """
		sel = self.viewConstraints.selectionModel()
		indexes = sel.selectedRows()
		if len(indexes) == 0:
			QMessageBox.information(self, "sorry", "nothing selected")
			return -1
		return indexes[0].row()


	def populateIndexes(self):
		indexes = self.table.indexes()
		if indexes == None:
			self.hideIndexes()
			return

		m = self.viewIndexes.model()
		m.clear()

		for idx in indexes:
			m.append( idx )

		for col in range(2):
			self.viewIndexes.resizeColumnToContents(col)

	def hideIndexes(self):
		index = self.tabs.indexOf(self.tabIndexes)
		if index >= 0:
			self.tabs.setTabEnabled(index, False)

	def createIndex(self):
		""" create an index """
		dlg = DlgCreateIndex(self, self.table)
		if not dlg.exec_():
			return
		self.refresh()

	def createSpatialIndex(self):
		""" asks for every geometry column whether it should create an index for it """
		# TODO: first check whether the index doesn't exist already
		QApplication.setOverrideCursor(Qt.WaitCursor)
		self.emit(SIGNAL("aboutToChangeTable()"))
		try:
			for fld in self.table.fields():
				if fld.dataType == 'geometry':
					res = QMessageBox.question(self, "create?", u"create spatial index for field %s?" % fld.name, QMessageBox.Yes | QMessageBox.No)
					if res == QMessageBox.Yes:
						self.table.createSpatialIndex(fld.name)
			self.refresh()
		except DbError, e:
			DlgDbError.showError(e, self)
			return
		finally:
			QApplication.restoreOverrideCursor()	
	
	def currentIndex(self):
		""" returns row index of selected index """
		sel = self.viewIndexes.selectionModel()
		indexes = sel.selectedRows()
		if len(indexes) == 0:
			QMessageBox.information(self, "sorry", "nothing selected")
			return -1
		return indexes[0].row()
	
	def deleteIndex(self):
		""" delete currently selected index """
		index = self.currentIndex()
		if index == -1:
			return

		m = self.viewIndexes.model()
		idx = m.getObject(index)

		res = QMessageBox.question(self, "are you sure", u"really delete index '%s' ?" % idx.name, QMessageBox.Yes | QMessageBox.No)
		if res != QMessageBox.Yes:
			return

		QApplication.setOverrideCursor(Qt.WaitCursor)
		self.emit(SIGNAL("aboutToChangeTable()"))
		try:
			idx.delete()
			self.refresh()
		except DbError, e:
			DlgDbError.showError(e, self)
			return
		finally:
			QApplication.restoreOverrideCursor()


