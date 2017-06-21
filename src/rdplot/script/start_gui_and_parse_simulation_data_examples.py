#!/usr/bin/python

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
import sys

from os.path import join
from os import listdir

from PyQt5 import QtWidgets

from os import path

from pathlib import Path

p =  path.abspath(path.join(__file__ ,"../../.."))

print(p)
sys.path.append(p)

from rdplot import Main

EXAMPLE_SIMULATION_DATA_PATH = "example_simulation_data"


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = Main()

    # Add all files and folders to the parser thread
    for file_name in listdir( EXAMPLE_SIMULATION_DATA_PATH ):
        main.simDataItemTreeView.parserThread.addPath(
            join( EXAMPLE_SIMULATION_DATA_PATH, file_name)
        )

    main.simDataItemTreeView.parserThread.run()

    # Start gui
    main.show()
    sys.exit(app.exec_())
