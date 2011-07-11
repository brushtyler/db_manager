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

from .db_plugins.plugin import DbError, Table
from .dlg_db_error import DlgDbError

class TableViewer(QTableView):
	def __init__(self, parent=None):
		QTableView.__init__(self, parent)
		self._clear()


	def refresh(self):
		self.loadData( self.item, True )

	def loadData(self, item, force=False):
		if item == self.item and not force: 
			return
		self._clear()

		self.item = item
		if isinstance(item, Table):
			self._loadTableData( item )

	def _clear(self):
		self.item = None

		# delete the old model
		model = self.model()
		self.setModel(None)
		if model: model.deleteLater()

	def _loadTableData(self, table):
		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
		try:
			# set the new model
			self.setModel( table.dataModel(self) )

		except DbError, e:
			QApplication.restoreOverrideCursor()
			DlgDbError.showError(e, self)

		else:
			self.update()
			QApplication.restoreOverrideCursor()


