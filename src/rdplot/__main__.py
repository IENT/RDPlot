#!/usr/bin/python3

##################################################################################################
#    This file is part of RDPlot - A gui for creating rd plots based on pyqt and matplotlib
#    <https://git.rwth-aachen.de/IENT-Software/rd-plot-gui>
#    Copyright (C) 2017  Institut fuer Nachrichtentechnik, RWTH Aachen University, GERMANY
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##################################################################################################
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize

from rdplot.Widgets import MainWindow

import pkg_resources
import sys

def main():

    app = QtWidgets.QApplication(sys.argv)

    # set icon of application
    app_icon = QtGui.QIcon()
    app_icon.addFile(pkg_resources.resource_filename(__name__,'logo/PLOT1024.png'), QSize(1024, 1024))
    app_icon.addFile(pkg_resources.resource_filename(__name__,'logo/PLOT512.png'), QSize(512, 512))
    app_icon.addFile(pkg_resources.resource_filename(__name__,'logo/PLOT256.png'), QSize(256, 256))
    app_icon.addFile(pkg_resources.resource_filename(__name__,'logo/PLOT128.png'), QSize(128, 128))
    app_icon.addFile(pkg_resources.resource_filename(__name__,'logo/PLOT64.png'), QSize(64, 64))
    app_icon.addFile(pkg_resources.resource_filename(__name__,'logo/PLOT32.png'), QSize(32, 32))
    app_icon.addFile(pkg_resources.resource_filename(__name__,'logo/PLOT16.png'), QSize(16, 16))
    app.setWindowIcon(app_icon)

    main_window = MainWindow.MainWindow()
    main_window.show()

    args = app.arguments()
    main_window.process_cmd_line_args(args)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()