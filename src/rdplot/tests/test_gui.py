import unittest
import sys
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
    def setUp(self):
        """Create the GUI"""
        self.app = QtWidgets.QApplication(sys.argv)
        self.main_window = Main()
        self.main_window.show()
        QTest.qWaitForWindowExposed(self.main_window)

    def test_process_cmd_line_args(self):
        with wait_signal(self.main_window.simDataItemTreeView.parserThread.allParsed, timeout=10000):
            self.main_window.process_cmd_line_args(['dummyAppName', path.join(TEST_DIR, 'test_logs/HM')])
        with wait_signal(self.main_window.simDataItemTreeView.parserThread.allParsed, timeout=10000):
            self.main_window.process_cmd_line_args(['dummyAppName', path.join(TEST_DIR, 'test_logs/SHM')])
        with wait_signal(self.main_window.simDataItemTreeView.parserThread.allParsed, timeout=10000):
            self.main_window.process_cmd_line_args(['dummyAppName', path.join(TEST_DIR, 'test_logs/JEM')])

    def tearDown(self):
        #EXIT
        self.main_window.close()
        self.app.exit()

if __name__ == '__main__':
    unittest.main()