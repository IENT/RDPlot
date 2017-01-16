#!/usr/bin/python

from main import Main
from model import EncLog

if __name__ == '__main__':
    import sys
    from PyQt5 import QtGui
    from PyQt5 import QtWidgets

    app = QtWidgets.QApplication(sys.argv)
    main = Main()

    main.encLogCollectionModelContainer.update(
        EncLog.parse_url('../simulation_examples/HEVC/')
    )
    # main.encLogCollectionModelContainer.update(
    #     EncLog.parse_url('../simulation_examples/hm360Lib/')
    # )

    main.show()
    sys.exit(app.exec_())
