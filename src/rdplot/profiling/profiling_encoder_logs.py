# this will reuse the test code written for the encoder logs in order to profile the parsing process
# might not be completely accurate, since this also profiles the test code
# result can be checked with snakeviz:
# pip install snakeviz
# snakeviz test_encoder_logs.stats on the command line

import unittest
import cProfile
import rdplot.tests.test_EncoderLogs

# load the test
suite = unittest.TestLoader().loadTestsFromTestCase(rdplot.tests.test_EncoderLogs.TestEncoderLogs)
# unittest.TextTestRunner().run(suite)

# run the profile on the test
cProfile.run('unittest.TextTestRunner().run(suite)', 'test_encoder_logs.stats')

