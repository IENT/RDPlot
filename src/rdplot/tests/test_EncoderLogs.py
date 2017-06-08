import unittest
from SimulationDataItemClasses import EncoderLogs
from os import path, listdir, walk

TEST_DIR = path.dirname(path.abspath(__file__))

class TestEncLogHM(unittest.TestCase):
    def setUp(self):
        hm_dir = path.join(TEST_DIR, 'test_logs/examplesForDifferentVersions/HM')
        hm_logs = listdir(hm_dir)
        self.hm_log_paths = [path.join(hm_dir, log) for log in hm_logs]

        pass

    def test_EncLogHM(self):
        self.hm_logs_parsed = [ EncoderLogs.EncLogHM(log) for log in self.hm_log_paths]
        for hm_parsed_instance in self.hm_logs_parsed:
            with self.subTest(instance=hm_parsed_instance):
                temporal_data = hm_parsed_instance.temporal_data
                summary_data = hm_parsed_instance.summary_data
                sequence = hm_parsed_instance.sequence
                config = hm_parsed_instance.config
                qp = hm_parsed_instance.qp

                # run checks on the parsed data
                # check variable types
                self.assertTrue(isinstance(sequence,str))
                self.assertTrue(path.isdir(config))
                self.assertTrue(isinstance(float(qp), float))

                # check structure of temporal data dict
                self.assertCountEqual(temporal_data.keys(), ['Frames', 'Bits', 'Y-PSNR', 'U-PSNR', 'V-PSNR'])


                # check structure of summary data dict
                # any stream will have at least summary and intra pictures:
                self.assertTrue('SUMMARY' in summary_data.keys())
                self.assertTrue('I' in summary_data.keys())
                for picture_type_key, data_keys in summary_data.items():
                    # check structure of  data dict for this picture type
                    self.assertCountEqual(data_keys, ['Total Frames', 'Y-PSNR', 'U-PSNR', 'V-PSNR', 'YUV-PSNR'])

    def test_can_parse_file(self):
        # try all log directories. only the one of HM logs should work, other should not work
        for x in walk(path.join(TEST_DIR, 'test_logs/examplesForDifferentVersions/')):
            log_dir = x[0]

            logs = listdir(log_dir)
            log_paths = [path.join(log_dir, log) for log in logs]

            for log_path in log_paths:
                with self.subTest(log_path=log_path):
                    if path.split(log_dir)[1] in ['HM', 'JEM']:
                        self.assertTrue(EncoderLogs.EncLogHM.can_parse_file(log_path))
                    else:
                        self.assertFalse(EncoderLogs.EncLogHM.can_parse_file(log_path))


                                                # def test_upper(self):
    #     self.assertEqual('foo'.upper(), 'FOO')
    #
    # def test_isupper(self):
    #     self.assertTrue('FOO'.isupper())
    #     self.assertFalse('Foo'.isupper())
    #
    # def test_split(self):
    #     s = 'hello world'
    #     self.assertEqual(s.split(), ['hello', 'world'])
    #     # check that s.split fails when the separator is not a string
    #     with self.assertRaises(TypeError):
    #         s.split(2)

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
                self.assertTrue(isinstance(sequence,str))
                self.assertTrue(path.isdir(config))

                self.assertTrue(isinstance(float(qps[0]), float))
                self.assertTrue(isinstance(float(qps[1]), float))

                # check structure of temporal data dict
                for layer_key, layer_data in temporal_data.items():
                    self.assertCountEqual(layer_data, ['Frames', 'Bits', 'Y-PSNR', 'U-PSNR', 'V-PSNR'])

                # check structure of summary data dict
                # any stream will have at least summary and intra pictures:
                self.assertTrue('SUMMARY' in summary_data.keys())
                self.assertTrue('I' in summary_data.keys())
                for picture_type_key, data_keys in summary_data.items():
                    # check structure of  data dict for this picture type
                    for layer_key, layer_data in data_keys.items():
                        self.assertCountEqual(layer_data, ['Frames', 'Bitrate', 'Y-PSNR', 'U-PSNR', 'V-PSNR', 'YUV-PSNR'])

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



if __name__ == '__main__':
    unittest.main()