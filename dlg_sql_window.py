# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .ui.DlgSqlWindow_ui import Ui_DlgSqlWindow

from .db_plugins.plugin import DbError
from .dlg_db_error import DlgDbError

class DlgSqlWindow(QDialog, Ui_DlgSqlWindow):

	def __init__(self, parent=None, db=None):
		QDialog.__init__(self, parent)
		self.db = db.connector
		self.setupUi(self)

		settings = QSettings()
		self.restoreGeometry(settings.value("/PostGIS_Manager/sql_geometry").toByteArray())
		
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
		settings.setValue("/PostGIS_Manager/sql_geometry", QVariant(self.saveGeometry()))
		
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
		try:
			model, secs, rowcount = self.db.getSqlTableModel( sql, self )
			self.viewResult.setModel( model )
			self.update()
			self.lblResult.setText("%d rows, %.1f seconds" % (rowcount, secs))
			QApplication.restoreOverrideCursor()
		
		except DbError, e:
			QApplication.restoreOverrideCursor()
			DlgDbError.showError(e, self)

