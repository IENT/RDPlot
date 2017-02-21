#!/usr/bin/python

import sys

from os.path import join
from os import listdir

from PyQt5 import QtWidgets
from main import Main



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
