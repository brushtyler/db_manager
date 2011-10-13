# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name                 : DB Manager
Description          : Database manager plugin for QuantumGIS
Date                 : May 23, 2011
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

from ui.DlgDbError_ui import Ui_DlgDbError

class DlgDbError(QDialog, Ui_DlgDbError):
	
	def __init__(self, e, parent=None):
		QDialog.__init__(self, parent)
		
		self.setupUi(self)
		
		msg = "<pre>" + e.msg.replace('<','&lt;') + "</pre>"
		self.txtMessage.setHtml(msg)
		if e.query != None:
			query = "<pre>" + e.query.replace('<','&lt;') + "</pre>"
			self.txtQuery.setHtml(query)


	@staticmethod
	def showError(e, parent=None):
		dlg = DlgDbError(e, parent)
		dlg.exec_()

