from os.path import (basename, dirname, abspath, join, sep, normpath, isdir,
                     isfile)
from glob import glob

import EncLogHM
import EncLogSHM
import EncLogHM360Lib
import EncLogHM360LibOld
import re


class SimulationDataItemFactory():
    # this dictionary stores the simulation types in a key value manner,
    # the key is a string which can be parsed from the log file and is unique
    # for a simulation type, the value is the class of the simulation type
    # for non unique keys, the order plays an important role!
    simTypeDict = [(r'Y-PSNR_VP0', EncLogHM360Lib.EncLogHM360Lib),
                   (r'^-----360 \s video \s parameters----', EncLogHM360LibOld.EncLogHM360LibOld),
                   (r'^SHM \s software', EncLogSHM.EncLogSHM),
                   (r'^HM \s software', EncLogHM.EncLogHM)
                   ]

    def _get_sim_type(self, path):
        try:
            for pattern, enclog in self.simTypeDict:
                with open(path, 'r') as log_file:
                    log_text = log_file.read()  # reads the whole text file
                    type = re.search(pattern, log_text, re.M + re.X)
                if type:
                    return enclog
        except:
            print("Dont be foolish. Do something useful here")

    # Check whether we have to parse dat directory or encoder logs
    # note, that it is only checked whether we are in a directory called 'dat'
    def _get_log_type(path):
        if basename(path) == 'dat':
            sim_data_type = 'dat'
        else:
            sim_data_type = 'encLog'
        return sim_data_type

    @classmethod
    def parse_directory(cls, directory_path):
        """Parse a directory for all encoder log files and return generator
           yielding :class: `EncLog`s"""
        if cls._get_log_type(directory_path) == 'encLog':
            paths = glob(join(directory_path, '*_enc.log'))
            return (cls._get_sim_type(cls, p)(p) for p in paths)
        else:
            print("Dont be foolish. Do something useful here")

    @classmethod
    def parse_directory_for_sequence(cls, sequence_file_path):
        """Parse a directory for encoder logs of a specific sequence given one
           encoder log of this sequence returning a generator yielding parsed
           encoder :class: `EncLog`s"""
        filename = basename(sequence_file_path)
        directory = dirname(sequence_file_path)
        sequence = filename.rsplit('_QP', 1)[0]

        # Search for other encoder logs in directory and parse them
        # TODO hardcoded file ending, needed to prevent ambiguous occurence
        # exceptions due to *.csv or other files being parsed
        paths = glob(directory + sep + sequence + '*_enc.log')
        return (cls._get_sim_type(cls, p)(p) for p in paths)

    @classmethod
    def create_instance_for_file(cls, file_path):
        return cls._get_sim_type(cls, file_path)(file_path)
