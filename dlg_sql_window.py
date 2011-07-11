# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .ui.DlgSqlWindow_ui import Ui_DlgSqlWindow

from .db_plugins.plugin import DbError
from .dlg_db_error import DlgDbError

class DlgSqlWindow(QDialog, Ui_DlgSqlWindow):

	def __init__(self, parent=None, db=None):
		QDialog.__init__(self, parent)
		self.db = db
		self.setupUi(self)

		settings = QSettings()
		self.restoreGeometry(settings.value("/DB_Manager/sqlWindow/geometry").toByteArray())
		
		self.connect(self.btnExecute, SIGNAL("clicked()"), self.executeSql)
		self.connect(self.btnClear, SIGNAL("clicked()"), self.clearSql)
		self.connect(self.buttonBox.button(QDialogButtonBox.Close), SIGNAL("clicked()"), self.close)

		# hide the load query as layer if feature is not supported
		loadAsLayerSupported = False and self.db.hasCustomQuerySupport()	# not implemented yet
		self.loadAsLayerGroup.setVisible( loadAsLayerSupported )
		if loadAsLayerSupported:
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

		try:
			# set the new model 
			model = self.db.sqlDataModel( sql, self )
			self.viewResult.setModel( model )
			self.lblResult.setText("%d rows, %.1f seconds" % (model.rowCount(), model.secs()))

		except DbError, e:
			QApplication.restoreOverrideCursor()
			DlgDbError.showError(e, self)

		else:
			self.update()
			QApplication.restoreOverrideCursor()

