import unittest
from rdplot.SimulationDataItemClasses import EncoderLogs, DatLogs
from rdplot.SimulationDataItem import AbstractSimulationDataItem
from rdplot.SimulationDataItem import SimulationDataItemFactory
# import SimulationDataItem
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


class TestEncoderLogs(unittest.TestCase):
    def setUp(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self._factory = SimulationDataItemFactory.from_path(
            SIMULATION_DATA_ITEM_CLASSES_PATH
        )
        test_log_path = path.join(TEST_DIR, 'test_logs/examplesForDifferentVersions')
        # list contents of directory, might include files
        files_and_folders_here = listdir(test_log_path)
        files_and_folders_here = [path.join(test_log_path, file_or_folder) for file_or_folder in files_and_folders_here]
        # remove files from list, we only want the log directories
        self.tested_log_dirs = [item for item in files_and_folders_here if path.isdir(item)]

        # build list of log files
        self.log_paths = []
        for log_dir in self.tested_log_dirs:
            logs = listdir(log_dir)
            logs = filter_by_ending(logs, 'log')
            self.log_paths += [path.join(log_dir, log) for log in logs]

        # set up a dictionary to record which parser were tested
        self.tested_parsers = {parser: False for parser in self._factory._classes}

        # remove base classes which are not tested
        del self.tested_parsers[AbstractSimulationDataItem]
        del self.tested_parsers[EncoderLogs.AbstractEncLog]
        del self.tested_parsers[DatLogs.AbstractDatLog]
        del self.tested_parsers[DatLogs.DatLogBasedOnClassName]
        del self.tested_parsers[EncoderLogs.EncLogVTM360Lib]

    def tearDown(self):
        self.app.exit()

    def test_parsing_of_logs(self):
        self.logs_parsed = []
        for log in self.log_paths:
            with self.subTest(log=log):
                self.logs_parsed += self._factory.create_item_from_file(log)

        for parsed_instance in self.logs_parsed:
            print(type(parsed_instance))
            with self.subTest(used_parser=parsed_instance):
                # record that a class was tested
                if type(parsed_instance) in self.tested_parsers:
                    self.tested_parsers[type(parsed_instance)] = True

                if isinstance(parsed_instance, EncoderLogs.EncLogHM):
                    temporal_data = parsed_instance.temporal_data
                    summary_data = parsed_instance.summary_data
                    sequence = parsed_instance.sequence
                    config = parsed_instance.config
                    qp = parsed_instance.qp

                    # run checks on the parsed data
                    # check variable types
                    self.assertTrue(isinstance(sequence, str))
                    self.assertTrue(path.isdir(config))
                    self.assertTrue(isinstance(float(qp), float))

                    # check structure of temporal data dict
                    self.assertCountEqual(temporal_data.keys(), ['Frames', 'ET', 'Bits', 'Y-PSNR', 'U-PSNR', 'V-PSNR'])

                    # check structure of summary data dict
                    # any stream will have at least summary and intra pictures:
                    self.assertTrue('SUMMARY' in summary_data.keys())
                    hm_major_version = summary_data['SUMMARY']['HM Major Version'][0][1]
                    if hm_major_version == 14:  # HM 14 does not write out average YUV-PSNR
                        self.assertTrue('I' in summary_data.keys())
                        for picture_type_key, data in summary_data.items():
                            # check structure of  data dict for this picture type
                            if picture_type_key == 'SUMMARY':
                                self.assertCountEqual(data.keys(), ['HM Major Version', 'Total Time', 'U-PSNR',
                                                                    'Y-PSNR', 'HM Minor Version', 'V-PSNR',
                                                                    'Total Frames'])
                            else:
                                self.assertCountEqual(data.keys(),
                                                      ['Total Frames', 'Y-PSNR', 'U-PSNR', 'V-PSNR'])

                    else:
                        self.assertTrue('I' in summary_data.keys())
                        for picture_type_key, data in summary_data.items():
                            # check structure of  data dict for this picture type
                            if picture_type_key == 'SUMMARY':
                                self.assertCountEqual(data.keys(), ['HM Major Version', 'Total Time', 'U-PSNR',
                                                                    'Y-PSNR', 'HM Minor Version', 'V-PSNR',
                                                                    'Total Frames', 'YUV-PSNR'])
                            else:
                                self.assertCountEqual(data.keys(),
                                                      ['Total Frames', 'Y-PSNR', 'U-PSNR', 'V-PSNR', 'YUV-PSNR'])
                elif isinstance(parsed_instance, EncoderLogs.EncLogHM360Lib):
                    temporal_data = parsed_instance.temporal_data
                    summary_data = parsed_instance.summary_data
                    sequence = parsed_instance.sequence
                    config = parsed_instance.config
                    qp = parsed_instance.qp

                    # run checks on the parsed data
                    # check variable types
                    self.assertTrue(isinstance(sequence, str))
                    self.assertTrue(path.isdir(config))
                    self.assertTrue(isinstance(float(qp), float))

                    # check structure of temporal data dict
                    self.assertCountEqual(temporal_data.keys(),
                                          ['Frames', 'ET', 'Bits', 'Y-PSNR', 'U-PSNR', 'V-PSNR', 'Y-SPSNR_NN',
                                           'U-SPSNR_NN',
                                           'V-SPSNR_NN', 'Y-WSPSNR', 'U-WSPSNR', 'V-WSPSNR', 'Y-SPSNR_I', 'U-SPSNR_I',
                                           'V-SPSNR_I', 'Y-CPPSNR', 'U-CPPSNR', 'V-CPPSNR', 'Y-E2EWSPSNR',
                                           'U-E2EWSPSNR',
                                           'V-E2EWSPSNR', 'Y-PSNR_VP0', 'U-PSNR_VP0', 'V-PSNR_VP0', 'Y-PSNR_VP1',
                                           'U-PSNR_VP1', 'V-PSNR_VP1'])

                    # check structure of summary data dict
                    # any stream will have at least summary and intra pictures:
                    self.assertTrue('SUMMARY' in summary_data.keys())
                    self.assertTrue('I Slices' in summary_data.keys())
                    for picture_type_key, data in summary_data.items():
                        # check structure of  data dict for this picture type
                        # will not check all elements, since this is configurable for 360Lib and cannot be known
                        if picture_type_key == 'SUMMARY':
                            self.assertIn('Total Frames', data.keys())
                            self.assertIn('Total Time', data.keys())
                            self.assertIn('Bitrate', data.keys())
                            self.assertIn('Y-PSNR', data.keys())
                            self.assertIn('U-PSNR', data.keys())
                            self.assertIn('V-PSNR', data.keys())
                            self.assertIn('YUV-PSNR', data.keys())
                        else:
                            self.assertIn('Total Frames', data.keys())
                            self.assertIn('Bitrate', data.keys())
                            self.assertIn('Y-PSNR', data.keys())
                            self.assertIn('U-PSNR', data.keys())
                            self.assertIn('V-PSNR', data.keys())
                            self.assertIn('YUV-PSNR', data.keys())

                elif isinstance(parsed_instance, EncoderLogs.EncLogSHM):
                    temporal_data = parsed_instance.temporal_data
                    summary_data = parsed_instance.summary_data
                    sequence = parsed_instance.sequence
                    config = parsed_instance.config
                    qps = parsed_instance.qp.split('+')

                    # run checks on the parsed data
                    # check variable types
                    self.assertTrue(isinstance(sequence, str))
                    self.assertTrue(path.isdir(config))

                    self.assertTrue(isinstance(float(qps[0]), float))
                    self.assertTrue(isinstance(float(qps[1]), float))

                    # check structure of temporal data dict
                    for layer_key, layer_data in temporal_data.items():
                        self.assertCountEqual(layer_data, ['Frames', 'ET', 'Bits', 'Y-PSNR', 'U-PSNR', 'V-PSNR'])

                    # check structure of summary data dict
                    # any stream will have at least summary and intra pictures:
                    self.assertTrue('SUMMARY' in summary_data.keys())
                    self.assertTrue('I' in summary_data.keys())
                    for picture_type_key, data_keys in summary_data.items():
                        # check structure of  data dict for this picture type
                        for layer_key, layer_data in data_keys.items():
                            if picture_type_key == 'SUMMARY':
                                self.assertCountEqual(layer_data.keys(),
                                                      ['Frames', 'Total Time', 'Bitrate', 'Y-PSNR', 'U-PSNR', 'V-PSNR',
                                                       'YUV-PSNR'])
                            else:
                                self.assertCountEqual(layer_data.keys(),
                                                      ['Frames', 'Bitrate', 'Y-PSNR', 'U-PSNR', 'V-PSNR',
                                                       'YUV-PSNR'])

                if isinstance(parsed_instance, DatLogs.DatLogBasedOnClassName):
                    summary_data = parsed_instance.summary_data
                    sequence = parsed_instance.sequence
                    config = parsed_instance.config
                    qp = parsed_instance.qp

                    # run checks on the parsed data
                    # check variable types
                    self.assertTrue(isinstance(sequence, str))
                    self.assertTrue(path.isdir(config))
                    self.assertTrue(isinstance(float(qp), float))

                    # no further checks possible, since the structure is defined by the xml format. not specific to a
                    # specific version

                # todo: need to add test code for these:
                elif isinstance(parsed_instance, DatLogs.DatLogHEVC):
                    # we are only testing concrete implementations, not the abstract base class
                    pass
                elif isinstance(parsed_instance, DatLogs.DatLogConversionPSNRLoss360):
                    # we are only testing concrete implementations, not the abstract base class
                    pass

                # these should not be tested
                elif isinstance(parsed_instance, AbstractSimulationDataItem):
                    # we are only testing concrete implementations, not the abstract base class
                    pass
                elif isinstance(parsed_instance, EncoderLogs.AbstractEncLog):
                    # we are only testing concrete implementations, not the abstract base class
                    pass
                elif isinstance(parsed_instance, DatLogs.AbstractDatLog):
                    # we are only testing concrete implementations, not the abstract base class
                    pass
                elif isinstance(parsed_instance, DatLogs.DatLogBasedOnClassName):
                    # we are only testing concrete implementations,
                    # this is also a base class which will not be used directly
                    pass

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
                    if cls.can_parse_file(log_path):
                        cls_list.append(cls(log_path))
                        break
                can_parse_file = True if cls_list else False
                self.assertTrue(can_parse_file)
                print('Can parse %s with %s' % (log_path, type(cls_list[0])))


if __name__ == '__main__':
    unittest.main()
