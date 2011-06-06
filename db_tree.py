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

from .db_model import DBModel

class DBTree(QTreeView):
	def __init__(self, parent=None):
		QTreeView.__init__(self, parent)
		self.setAttribute(Qt.WA_DeleteOnClose)
		self.setModel( DBModel() )

	def refresh(self, selectedItemOnly=False):
		self.model().refresh(selectedItemOnly)

	def currentItem(self):
		indexes = self.selectedIndexes()
		if len(indexes) <= 0:
			return
		return self.model().getItem(indexes[0])

