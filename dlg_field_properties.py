
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .db_plugins.plugin import TableField

from ui.DlgFieldProperties_ui import Ui_DlgFieldProperties

class DlgFieldProperties(QDialog, Ui_DlgFieldProperties):
	
	def __init__(self, parent=None, fld=None, table=None, db=None):
		QDialog.__init__(self, parent)
		self.fld = fld
		self.table = self.fld.table() if self.fld and self.fld.table() else table
		self.db = self.table.database() if self.table and self.table.database() else db
		self.setupUi(self)
		
		for item in self.db.connector.fieldTypes():
			self.cboType.addItem(item)
		self.setField(self.fld)

		self.connect(self.buttonBox, SIGNAL("accepted()"), self.onOK)

	def setField(self, fld):
		if fld == None:
			return
		self.editName.setText(fld.name)
		self.cboType.setEditText(fld.dataType)
		if fld.modifier:
			self.editLength.setText(unicode(fld.modifier))
		self.chkNull.setChecked(not fld.notNull)
		if fld.hasDefault:
			self.editDefault.setText(fld.default)

	def getField(self, newCopy=False):
		if not self.fld or newCopy:
			self.fld = TableField(self.table)
		self.fld.name = self.editName.text()
		self.fld.dataType = self.cboType.currentText()
		self.fld.notNull = not self.chkNull.isChecked()
		self.fld.default = self.editDefault.text()
		self.fld.hasDefault = self.fld.default != ""
		modifier, ok = self.editLength.text().toInt()
		self.fld.modifier = modifier if ok else None
		return self.fld


	def onOK(self):
		""" first check whether everything's fine """
		fld = self.getField()
		if fld.name == "":
			QMessageBox.critical(self, "sorry", "field name must not be empty")
			return
		if fld.dataType == "":
			QMessageBox.critical(self, "sorry", "field type must not be empty")
			return
		
		self.accept()

