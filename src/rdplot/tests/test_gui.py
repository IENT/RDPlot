import unittest
import sys
import random
from os import path, listdir, walk
from contextlib import contextmanager
from PyQt5 import QtGui, QtCore
from PyQt5.QtTest import QTest
from PyQt5 import QtWidgets
from rdplot.Widgets.MainWindow import MainWindow

from time import sleep

TEST_DIR = path.dirname(path.abspath(__file__))

@contextmanager
def wait_signal(signal, timeout=10000):
    """Block loop until signal emitted, or timeout (ms) elapses.
    see https://www.jdreaver.com/posts/2014-07-03-waiting-for-signals-pyside-pyqt.html
    """
    loop = QtCore.QEventLoop()
    signal.connect(loop.quit)

    yield

    if timeout is not None:
        QtCore.QTimer.singleShot(timeout, loop.quit)
    loop.exec_()


class TestMain(unittest.TestCase):
    """Start the GUI, once load all example simulation directories and rd data, then exit."""
    def setUp(self):
        """Create the GUI"""
        return
        self.app = QtWidgets.QApplication(sys.argv)
        self.main_window = MainWindow()
        # catch invoked message boxes for additional parameters and make random selection
        self.main_window.simDataItemTreeModel.dialog.message_shown.connect(self.random_attributes_selection)
        self.main_window.show()
        QTest.qWaitForWindowExposed(self.main_window)

    def test_process_cmd_line_args(self):
        # load all found logs and rd-data
        # try all log directories.
        return
        sim_dirs_root = path.join(TEST_DIR, 'test_logs/exampleSimLogDirs/')
        sim_dirs = listdir(sim_dirs_root)
        sim_dirs = [path.join(sim_dirs_root, dir) for dir in sim_dirs]
        for sim_dir in sim_dirs:
            with wait_signal(self.main_window.simDataItemTreeView.parserThread.allParsed, timeout=10000):
                self.main_window.process_cmd_line_args(['dummyAppName', sim_dir])

        # try all rd-data
        rd_data_root = path.join(TEST_DIR, 'test_logs/exampleRDData/')
        rd_data_files = listdir(rd_data_root)
        rd_data_files = [path.join(rd_data_root, file) for file in rd_data_files]
        for rd_data_file in rd_data_files:
            with wait_signal(self.main_window.simDataItemTreeView.parserThread.allParsed, timeout=10000):
                self.main_window.process_cmd_line_args(['dummyAppName', rd_data_file])

        # try all dat log directories
        rd_data_root = path.join(TEST_DIR, 'test_logs/exampleDatLogDirs/')
        rd_data_files = listdir(rd_data_root)
        rd_data_files = [path.join(rd_data_root, file) for file in rd_data_files]

        for rd_data_file in rd_data_files:
            with wait_signal(self.main_window.simDataItemTreeView.parserThread.allParsed, timeout=10000):
                self.main_window.process_cmd_line_args(['dummyAppName', rd_data_file])

    def random_attributes_selection(self):
        return 
        for i in range(random.randint(0, len(self.main_window.simDataItemTreeModel.dialog.not_chosen_par)-1)):
            rnd_nmbr = random.randint(0, len(self.main_window.simDataItemTreeModel.dialog.not_chosen_par)-1)
            rnd_item = self.main_window.simDataItemTreeModel.dialog.not_chosen_par.item(rnd_nmbr)
            if not self.main_window.simDataItemTreeModel.dialog.chosen_par.findItems(rnd_item.text(), QtCore.Qt.MatchExactly):
                self.main_window.simDataItemTreeModel.dialog.chosen_par.addItems([rnd_item.text()])
                self.main_window.simDataItemTreeModel.dialog.not_chosen_par.takeItem(rnd_nmbr)
        self.main_window.simDataItemTreeModel.dialog.accept()

    def tearDown(self):
        return
        #EXIT
        self.app.exit()
        self.main_window.close()


if __name__ == '__main__':
    unittest.main()
