import unittest
from rdplot.SimulationDataItemClasses import EncoderLogs, CsvLogs
from rdplot.SimulationDataItem import SimulationDataItemFactory
from os import path, listdir
from PyQt5 import QtWidgets
import sys

# path to test module (this file)
TEST_DIR = path.dirname(path.abspath(__file__))

# Path to the folder containing simulation data sub classes. The classes
# are loaded by the simulation data item factory and used for parsing files
SIMULATION_DATA_ITEM_CLASSES_PATH = path.normpath(path.join(TEST_DIR, '../SimulationDataItemClasses'))


def filter_by_ending(paths, value):
    """
    Filter file paths, remove paths, file ending does not match
    :param paths: list of file paths
    :param value: file ending
    :return: paths which have matching file ending
    """
    for a_path in paths:
        if '.' in a_path:
            dont_care, ending = a_path.rsplit('.', maxsplit=1)
            if ending == value:
                yield a_path


class TestCsvLogs(unittest.TestCase):
    def setUp(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self._factory = SimulationDataItemFactory.from_path(
            SIMULATION_DATA_ITEM_CLASSES_PATH
        )
        test_log_path = path.join(TEST_DIR, 'test_logs/exampleCsv')
        # list contents of directory, might include files
        files_and_folders_here = listdir(test_log_path)
        files_and_folders_here = [path.join(test_log_path, file_or_folder) for file_or_folder in files_and_folders_here]
        # remove files from list, we only want the log directories
        self.tested_log_dirs = [item for item in files_and_folders_here if path.isdir(item)]

        # build list of log files
        self.log_paths = []
        for log_dir in self.tested_log_dirs:
            logs = listdir(log_dir)
            logs = filter_by_ending(logs, 'csv')
            self.log_paths += [path.join(log_dir, log) for log in logs]

        # set up a dictionary to record which parser were tested
        self.tested_parsers = {CsvLogs.CSVLog: False}

    def tearDown(self):
        self.app.deleteLater()
        self.app.exit()

    def test_parsing_of_logs(self):
        self.logs_parsed = []
        for log in self.log_paths:
            with self.subTest(log=log):
                self.logs_parsed += self._factory.create_item_list_from_path(log)

        for parsed_instance in self.logs_parsed:
            print(type(parsed_instance))
            with self.subTest(used_parser=parsed_instance):
                # record that a class was tested
                if type(parsed_instance) in self.tested_parsers:
                    self.tested_parsers[type(parsed_instance)] = True

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

                    # no further checks possible, since the structure is defined by the csv format. not specific to a
                    # specific version

                # no parser was used. we found a bug
                else:
                    self.fail('No test code for %s. Add code to test the parser %s.'
                              % (parsed_instance, type(parsed_instance)))

        # confirm that all parsers were tested.
        # this will be triggered if there is a test implementation, but no logs to do the testing with
        for parser, was_tested in self.tested_parsers.items():
            if not was_tested:
                # only testing encoder logs here
                if not issubclass(parser, EncoderLogs.AbstractEncLog):
                    continue
                self.fail('%s was not tested! Did you add log files for it?' % parser)

    def test_if_suitable_parser_exits(self):
        for log_path in self.log_paths:
            with self.subTest(log_path=log_path):
                cls_list = []
                # try parser, in the order given by their parse_order attribute.
                # use the first one that can parse the file
                for cls in reversed(sorted(self._factory._classes, key=lambda parser_class: parser_class.parse_order)):
                    if cls.can_parse_file(log_path) and log_path.endswith(".csv"):
                        cls_list.append(self._factory.parse_csv_item_list(log_path))
                        break
                    if cls.can_parse_file(log_path):
                        cls_list.append(cls(log_path))
                        break
                can_parse_file = True if cls_list else False
                self.assertTrue(can_parse_file)
                print('Can parse %s with %s' % (log_path, type(cls_list[0])))


if __name__ == '__main__':
    unittest.main()
