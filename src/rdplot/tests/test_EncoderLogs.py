import unittest
from rdplot.SimulationDataItemClasses import EncoderLogs
import rdplot.SimulationDataItem
from os import path, listdir, walk

TEST_DIR = path.dirname(path.abspath(__file__))


class TestEncLogHM(unittest.TestCase):
    def setUp(self):
        hm_dir = path.join(TEST_DIR, 'test_logs/examplesForDifferentVersions/HM')
        hm_logs = listdir(hm_dir)
        self.hm_log_paths = [path.join(hm_dir, log) for log in hm_logs]

        pass

    def test_EncLogHM(self):
        self.hm_logs_parsed = [EncoderLogs.EncLogHM(log) for log in self.hm_log_paths]
        for hm_parsed_instance in self.hm_logs_parsed:
            with self.subTest(instance=hm_parsed_instance):
                temporal_data = hm_parsed_instance.temporal_data
                summary_data = hm_parsed_instance.summary_data
                sequence = hm_parsed_instance.sequence
                config = hm_parsed_instance.config
                qp = hm_parsed_instance.qp

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

    def test_can_parse_file(self):
        # try all log directories. only the one of HM logs should work, other should not work
        for x in walk(path.join(TEST_DIR, 'test_logs/examplesForDifferentVersions/')):
            log_dir = x[0]

            logs = listdir(log_dir)
            log_paths = [path.join(log_dir, log) for log in logs]

            for log_path in log_paths:
                with self.subTest(log_path=log_path):
                    if path.split(log_dir)[1] in ['HM', 'JEM', 'HM360Lib']:
                        # todo: should write parser such, that he can detect only HM and exclude the others?
                        self.assertTrue(EncoderLogs.EncLogHM.can_parse_file(log_path))
                    else:
                        self.assertFalse(EncoderLogs.EncLogHM.can_parse_file(log_path))


class TestEncLogSHM(unittest.TestCase):
    def setUp(self):
        shm_dir = path.join(TEST_DIR, 'test_logs/examplesForDifferentVersions/SHM')
        shm_logs = listdir(shm_dir)
        self.shm_log_paths = [path.join(shm_dir, log) for log in shm_logs]

        pass

    def test_EncLogSHM(self):
        self.shm_logs_parsed = [EncoderLogs.EncLogSHM(log) for log in self.shm_log_paths]
        for shm_parsed_instance in self.shm_logs_parsed:
            with self.subTest(instance=shm_parsed_instance):
                temporal_data = shm_parsed_instance.temporal_data
                summary_data = shm_parsed_instance.summary_data
                sequence = shm_parsed_instance.sequence
                config = shm_parsed_instance.config
                qps = shm_parsed_instance.qp.split(' ')

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

    def test_can_parse_file(self):
        # try all log directories. only the one of HM logs should work, other should not work
        for x in walk(path.join(TEST_DIR, 'test_logs/examplesForDifferentVersions/')):
            log_dir = x[0]

            logs = listdir(log_dir)
            log_paths = [path.join(log_dir, log) for log in logs]

            for log_path in log_paths:
                with self.subTest(log_path=log_path):
                    if path.split(log_dir)[1] in ['SHM']:
                        self.assertTrue(EncoderLogs.EncLogSHM.can_parse_file(log_path))
                    else:
                        self.assertFalse(EncoderLogs.EncLogSHM.can_parse_file(log_path))


class TestEncLogHM360Lib(unittest.TestCase):
    def setUp(self):
        log_dir = path.join(TEST_DIR, 'test_logs/examplesForDifferentVersions/HM360Lib')
        logs = listdir(log_dir)
        self.log_paths = [path.join(log_dir, log) for log in logs]

        pass

    def test_EncLogHM360Lib(self):
        self.logs_parsed = [EncoderLogs.EncLogHM360Lib(log) for log in self.log_paths]
        for parsed_instance in self.logs_parsed:
            with self.subTest(instance=parsed_instance):
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
                                      ['Frames', 'ET', 'Bits', 'Y-PSNR', 'U-PSNR', 'V-PSNR', 'Y-SPSNR_NN', 'U-SPSNR_NN',
                                       'V-SPSNR_NN', 'Y-WSPSNR', 'U-WSPSNR', 'V-WSPSNR', 'Y-SPSNR_I', 'U-SPSNR_I',
                                       'V-SPSNR_I', 'Y-CPPSNR', 'U-CPPSNR', 'V-CPPSNR', 'Y-E2EWSPSNR', 'U-E2EWSPSNR',
                                       'V-E2EWSPSNR', 'Y-PSNR_VP0', 'U-PSNR_VP0', 'V-PSNR_VP0', 'Y-PSNR_VP1',
                                       'U-PSNR_VP1', 'V-PSNR_VP1'])

                # check structure of summary data dict
                # any stream will have at least summary and intra pictures:
                self.assertTrue('SUMMARY' in summary_data.keys())
                self.assertTrue('I' in summary_data.keys())
                for picture_type_key, data in summary_data.items():
                    # check structure of  data dict for this picture type
                    if picture_type_key == 'SUMMARY':
                        self.assertCountEqual(data.keys(),
                                              ['Frames', 'Total Time', 'Bitrate', 'Y-PSNR', 'U-PSNR', 'V-PSNR',
                                               'YUV-PSNR',
                                               'Y-WSPSNR', 'U-WSPSNR', 'V-WSPSNR',
                                               'Y-E2ESPSNR_NN', 'U-E2ESPSNR_NN', 'V-E2ESPSNR_NN',
                                               'Y-E2ESPSNR_I', 'U-E2ESPSNR_I', 'V-E2ESPSNR_I',
                                               'Y-E2ECPPPSNR', 'U-E2ECPPPSNR', 'V-E2ECPPPSNR', 'Y-E2EWSPSNR',
                                               'U-E2EWSPSNR', 'V-E2EWSPSNR',
                                               'Y-PSNR_DYN_VP0', 'U-PSNR_DYN_VP0', 'V-PSNR_DYN_VP0',
                                               'Y-PSNR_DYN_VP1', 'U-PSNR_DYN_VP1',
                                               'V-PSNR_DYN_VP1', 'Y-CFSPSNR_NN', 'U-CFSPSNR_NN',
                                               'V-CFSPSNR_NN', 'Y-CFSPSNR_I', 'U-CFSPSNR_I',
                                               'V-CFSPSNR_I', 'Y-CFCPPPSNR', 'U-CFCPPPSNR', 'V-CFCPPPSNR'])
                    else:
                        self.assertCountEqual(data.keys(),
                                              ['Frames', 'Bitrate', 'Y-PSNR', 'U-PSNR', 'V-PSNR',
                                               'YUV-PSNR',
                                               'Y-WSPSNR', 'U-WSPSNR', 'V-WSPSNR',
                                               'Y-E2ESPSNR_NN', 'U-E2ESPSNR_NN', 'V-E2ESPSNR_NN',
                                               'Y-E2ESPSNR_I', 'U-E2ESPSNR_I', 'V-E2ESPSNR_I',
                                               'Y-E2ECPPPSNR', 'U-E2ECPPPSNR', 'V-E2ECPPPSNR', 'Y-E2EWSPSNR',
                                               'U-E2EWSPSNR', 'V-E2EWSPSNR',
                                               'Y-PSNR_DYN_VP0', 'U-PSNR_DYN_VP0', 'V-PSNR_DYN_VP0',
                                               'Y-PSNR_DYN_VP1', 'U-PSNR_DYN_VP1',
                                               'V-PSNR_DYN_VP1', 'Y-CFSPSNR_NN', 'U-CFSPSNR_NN',
                                               'V-CFSPSNR_NN', 'Y-CFSPSNR_I', 'U-CFSPSNR_I',
                                               'V-CFSPSNR_I', 'Y-CFCPPPSNR', 'U-CFCPPPSNR', 'V-CFCPPPSNR'])

    def test_can_parse_file(self):
        # try all log directories. only the one of HM logs should work, other should not work
        for x in walk(path.join(TEST_DIR, 'test_logs/examplesForDifferentVersions/')):
            log_dir = x[0]

            logs = listdir(log_dir)
            log_paths = [path.join(log_dir, log) for log in logs]

            for log_path in log_paths:
                with self.subTest(log_path=log_path):
                    if path.split(log_dir)[1] in ['HM360Lib']:
                        self.assertTrue(EncoderLogs.EncLogHM360Lib.can_parse_file(log_path))
                    else:
                        self.assertFalse(EncoderLogs.EncLogHM360Lib.can_parse_file(log_path))


if __name__ == '__main__':
    unittest.main()
