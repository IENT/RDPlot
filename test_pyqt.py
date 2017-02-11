#!/usr/bin/python

from main import Main
from model import SimDataItem

if __name__ == '__main__':
    import sys
    from PyQt5 import QtGui
    from PyQt5 import QtWidgets

    app = QtWidgets.QApplication(sys.argv)
    main = Main()

    main.simDataItemTreeModel.update(
        SimDataItem.parse_url('../simulation_examples/HEVC/')
    )
    # main.simDataItemTreeModel.update(
    #     SimDataItem.parse_url('../simulation_examples/hm360Lib/')
    # )

    main.show()
    sys.exit(app.exec_())
