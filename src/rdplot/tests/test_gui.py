import unittest
import sys
import random
from os import path, listdir, walk
from contextlib import contextmanager
from PyQt5 import QtGui, QtCore
from PyQt5.QtTest import QTest
from PyQt5 import QtWidgets
from rdplot import Main

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
        self.app = QtWidgets.QApplication(sys.argv)
        self.main_window = Main()
        self.main_window.show()
        QTest.qWaitForWindowExposed(self.main_window)

    def test_process_cmd_line_args(self):
        # load all found logs and rd-data

        # try all log directories.
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

    def tearDown(self):
        #EXIT
        self.main_window.close()
        self.app.exit()


class FuzzTestGUI(unittest.TestCase):
    """ 1. Start the GUI,
        2. load a few randomly selected log directories or rd-data
        3. randomly select something from sequences and plot settings; do this several times
        4. repeat from 2. Do this for a given number of iterations
    """
    def setUp(self):
        """Create the GUI"""
        self.app = QtWidgets.QApplication(sys.argv)
        self.main_window = Main()
        self.main_window.show()
        QTest.qWaitForWindowExposed(self.main_window)

    def test_fuzz_plot(self):
        # find all logs and rd-data

        # find all sim dirs
        sim_dirs_root = path.join(TEST_DIR, 'test_logs/exampleSimLogDirs/')
        sim_dirs = listdir(sim_dirs_root)
        sim_dirs = [path.join(sim_dirs_root, dir) for dir in sim_dirs]
        # find all rd-data
        rd_data_root = path.join(TEST_DIR, 'test_logs/exampleRDData/')
        rd_data_files = listdir(rd_data_root)
        rd_data_files = [path.join(rd_data_root, file) for file in rd_data_files]

        all_data = sim_dirs + rd_data_files

        # randomly choose 3 items from all data
        random_sim_items = random.sample(all_data, 3)

        # add the chosen items
        for item in random_sim_items:
            with wait_signal(self.main_window.simDataItemTreeView.parserThread.allParsed, timeout=10000):
                self.main_window.process_cmd_line_args(['dummyAppName', item])

        # now fuzz the gui
        # todo

    def tearDown(self):
        #EXIT
        self.main_window.close()
        self.app.exit()

if __name__ == '__main__':
    unittest.main()