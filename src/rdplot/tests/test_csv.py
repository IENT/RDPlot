import unittest
from rdplot.SimulationDataItemClasses import CsvLogs
from rdplot.SimulationDataItem import SimulationDataItemFactory
from PyQt5 import QtWidgets
from os import path, listdir
import sys

# path to test module (this file)
TEST_DIR = path.dirname(path.abspath(__file__))

class TestCsvLogs(unittest.TestCase):
    def setUp(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self._factory = SimulationDataItemFactory.from_path('../SimulationDataItemClasses')
        test_log_path = path.join(TEST_DIR, 'test_logs/exampleCsv')
        self.logs_parsed = self._factory.create_item_list_from_directory(test_log_path)

    def tearDown(self):
        self.app.exit()

    def test_parsing_of_logs(self):
        for parsed_instance in self.logs_parsed:
            print(type(parsed_instance))
            with self.subTest(used_parser=parsed_instance):
                if isinstance(parsed_instance, CsvLogs.CSVLog):
                    summary_data = parsed_instance.summary_data
                    sequence = parsed_instance.sequence
                    config = parsed_instance.config
                    qp = parsed_instance.qp

                    # run checks on the parsed data
                    # check variable types
                    self.assertTrue(isinstance(sequence, str))
                    self.assertTrue(isinstance(config, str))
                    self.assertTrue(isinstance(float(qp), float))

if __name__ == '__main__':
    unittest.main()
