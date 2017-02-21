#!/usr/bin/python

import sys

from PyQt5 import QtWidgets
from main import Main


# Call this from rd-plot-gui folder with
# >>> python -m script.start_gui_and_parse_simulation_examples

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = Main()


    main.simDataItemTreeView.parserThread.addPath(
        '../simulation_examples/HEVC/log'
    )
    main.simDataItemTreeView.parserThread.addPath(
        '../simulation_examples/hm360Lib/log'
    )
    main.simDataItemTreeView.parserThread.addPath(
        '../simulation_examples/SHVC/log'
    )

    main.simDataItemTreeView.parserThread.run()


    main.show()
    sys.exit(app.exec_())
