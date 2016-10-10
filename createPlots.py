# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'createPlots.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
import sys

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_createPlots(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.setupUi(self)
        
    def setupUi(self, createPlots):
        createPlots.setObjectName(_fromUtf8("createPlots"))
        createPlots.resize(712, 531)
        self.centralwidget = QtGui.QWidget(createPlots)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.widget = QtGui.QWidget(self.centralwidget)
        self.widget.setObjectName(_fromUtf8("widget"))
        self.horizontalLayout_2.addWidget(self.widget)
        createPlots.setCentralWidget(self.centralwidget)
        self.statusbar = QtGui.QStatusBar(createPlots)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        createPlots.setStatusBar(self.statusbar)
        self.menubar = QtGui.QMenuBar(createPlots)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 712, 25))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        self.menuView = QtGui.QMenu(self.menubar)
        self.menuView.setObjectName(_fromUtf8("menuView"))
        createPlots.setMenuBar(self.menubar)
        self.PlaylistWidget = QtGui.QDockWidget(createPlots)
        self.PlaylistWidget.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea)
        self.PlaylistWidget.setObjectName(_fromUtf8("PlaylistWidget"))
        self.dockWidgetContents = QtGui.QWidget()
        self.dockWidgetContents.setObjectName(_fromUtf8("dockWidgetContents"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setSizeConstraint(QtGui.QLayout.SetMaximumSize)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.DisplayPlaylist = QtGui.QTreeView(self.dockWidgetContents)
        self.DisplayPlaylist.setAcceptDrops(False)
        self.DisplayPlaylist.setObjectName(_fromUtf8("DisplayPlaylist"))
        self.verticalLayout.addWidget(self.DisplayPlaylist)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.OpenDir = QtGui.QPushButton(self.dockWidgetContents)
        self.OpenDir.setObjectName(_fromUtf8("OpenDir"))
        self.horizontalLayout.addWidget(self.OpenDir)
        self.OpenFile = QtGui.QPushButton(self.dockWidgetContents)
        self.OpenFile.setObjectName(_fromUtf8("OpenFile"))
        self.horizontalLayout.addWidget(self.OpenFile)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.PlaylistWidget.setWidget(self.dockWidgetContents)
        createPlots.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.PlaylistWidget)
        self.plotsettings = QtGui.QDockWidget(createPlots)
        self.plotsettings.setEnabled(True)
        self.plotsettings.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        self.plotsettings.setObjectName(_fromUtf8("plotsettings"))
        self.dockWidgetContents_2 = QtGui.QWidget()
        self.dockWidgetContents_2.setObjectName(_fromUtf8("dockWidgetContents_2"))
        self.plotsettings.setWidget(self.dockWidgetContents_2)
        createPlots.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.plotsettings)
        self.actionOpen_File = QtGui.QAction(createPlots)
        self.actionOpen_File.setObjectName(_fromUtf8("actionOpen_File"))
        self.actionOpen_Directory = QtGui.QAction(createPlots)
        self.actionOpen_Directory.setObjectName(_fromUtf8("actionOpen_Directory"))
        self.actionSave_Plot = QtGui.QAction(createPlots)
        self.actionSave_Plot.setObjectName(_fromUtf8("actionSave_Plot"))
        self.actionHide_Playlist = QtGui.QAction(createPlots)
        self.actionHide_Playlist.setCheckable(True)
        self.actionHide_Playlist.setChecked(False)
        self.actionHide_Playlist.setObjectName(_fromUtf8("actionHide_Playlist"))
        self.actionHide_PlotSettings = QtGui.QAction(createPlots)
        self.actionHide_PlotSettings.setCheckable(True)
        self.actionHide_PlotSettings.setObjectName(_fromUtf8("actionHide_PlotSettings"))
        self.actionSave_all_Plots = QtGui.QAction(createPlots)
        self.actionSave_all_Plots.setObjectName(_fromUtf8("actionSave_all_Plots"))
        self.actionExit = QtGui.QAction(createPlots)
        self.actionExit.setObjectName(_fromUtf8("actionExit"))
        self.menuFile.addAction(self.actionOpen_File)
        self.menuFile.addAction(self.actionOpen_Directory)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionSave_Plot)
        self.menuFile.addAction(self.actionSave_all_Plots)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuView.addAction(self.actionHide_Playlist)
        self.menuView.addAction(self.actionHide_PlotSettings)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuView.menuAction())

        self.retranslateUi(createPlots)
        QtCore.QObject.connect(self.actionHide_Playlist, QtCore.SIGNAL(_fromUtf8("triggered(bool)")), self.PlaylistWidget.setHidden)
        QtCore.QObject.connect(self.actionHide_Playlist, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.PlaylistWidget.setVisible)
        QtCore.QObject.connect(self.actionHide_PlotSettings, QtCore.SIGNAL(_fromUtf8("triggered(bool)")), self.plotsettings.setHidden)
        QtCore.QObject.connect(self.actionHide_PlotSettings, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.plotsettings.setVisible)
        QtCore.QObject.connect(self.actionExit, QtCore.SIGNAL(_fromUtf8("activated()")), createPlots.close)
        QtCore.QMetaObject.connectSlotsByName(createPlots)

    def retranslateUi(self, createPlots):
        createPlots.setWindowTitle(_translate("createPlots", "createPlots", None))
        self.menuFile.setTitle(_translate("createPlots", "File", None))
        self.menuView.setTitle(_translate("createPlots", "View", None))
        self.PlaylistWidget.setWindowTitle(_translate("createPlots", "Playlist", None))
        self.OpenDir.setText(_translate("createPlots", "Open Directory", None))
        self.OpenFile.setText(_translate("createPlots", "Open File", None))
        self.plotsettings.setWindowTitle(_translate("createPlots", "Plotsettings", None))
        self.actionOpen_File.setText(_translate("createPlots", "Open File", None))
        self.actionOpen_Directory.setText(_translate("createPlots", "Open Directory", None))
        self.actionSave_Plot.setText(_translate("createPlots", "Save Plot", None))
        self.actionHide_Playlist.setText(_translate("createPlots", "Hide Playlist", None))
        self.actionHide_PlotSettings.setText(_translate("createPlots", "Hide Plotsettings", None))
        self.actionSave_all_Plots.setText(_translate("createPlots", "Save all Plots", None))
        self.actionExit.setText(_translate("createPlots", "Exit", None))


app = QtGui.QApplication(sys.argv)
ex = Ui_createPlots()
ex.show()
sys.exit(app.exec_())
