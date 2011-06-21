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
