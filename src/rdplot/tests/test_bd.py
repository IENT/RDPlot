import unittest
import sys
from rdplot.lib.BD import bjontegaard
from PyQt5 import QtWidgets


class TestBD(unittest.TestCase):

    def setUp(self):
        # set up inputs and outputs
        self.app = QtWidgets.QApplication(sys.argv)
        # Notiz: Kurve mit nur vier Punkten erstellen; Ergebnisse mit Matlab vergleichen
        self.curve1 = [(937.0112, 45.5074), (1405.4792, 47.0002), (3438.7128, 49.9565), (6448.6368, 52.1459)]
        self.curve2 = [(822.0064, 45.7215), (1608.9144, 47.6227), (3086.912, 50.1394), (5784.7696, 52.3339)]
        self.output_rate = -11.8353612757205
        self.output_dsnr = 0.425738970169449

    def tearDown(self):
        self.app.exit()

    def testBjontegaard(self):
        with self.subTest(mode='drate'):
            self.assertAlmostEqual(bjontegaard(self.curve1, self.curve2, mode='drate', testmode=True), self.output_rate, delta=0.01)
        with self.subTest(mode='dsnr'):
            self.assertAlmostEqual(bjontegaard(self.curve1, self.curve2, mode='dsnr', testmode=True), self.output_dsnr, delta=0.01)


if __name__ == '__main__':
    unittest.main()