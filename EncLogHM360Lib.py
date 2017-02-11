from model import (EncLog, EncLogParserError)

from os.path import (basename,sep, normpath)
import re

class EncLogHM360Lib(EncLog):
    def __init__(self, path):
        super().__init__(path)

    def _parse_path(self,path):
        try:
            # Assumes structure of .../<simulation_directory>/log/<basename>
            directories = normpath(path).split(sep)[0: -2]
            filename    = basename(path)
        except IndexError:
            raise EncLogParserError(
                "Path {} can not be splitted into directories and filename"
                .format(filename, path)
            )

        try:
            seperator = '-'
            filename_splitted = filename.split('_QP')[0].split(seperator)
            sequence = filename_splitted[-1]
            config = seperator.join(filename_splitted[0: -2])
        except IndexError:
            raise EncLogParserError((
                "Filename {} can not be splitted into config until '{}' and"
                " sequence between last '{}' and '_QP'"
            ).format(filename, seperator, seperator))

        # prepend simulation directory to config
        config = directories[-1] + ' ' + config
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            qp = re.findall(r""" ^QP \s+ : \s+ (\d+.\d+) $
                                  """, log_text, re.M + re.X)
        qp = qp[0]
        return sequence, config, qp

    def _parse_summary_data(self):
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            summaries = re.findall(r""" ^(\S+) .+ $ \s .+ $
                                        \s+ (\d+) \s+ \D \s+ (\S+)  # Total Frames, Bitrate
                                        \s+ (\S+) \s+ (\S+) \s+ (\S+) \s+ (\S+)  # y-, u-, v-, yuv-PSNR
                                        \s+ (\S+) \s+ (\S+) \s+ (\S+)  # SPSNR_NN
                                        \s+ (\S+) \s+ (\S+) \s+ (\S+)  # WSPSNR
                                        \s+ (\S+) \s+ (\S+) \s+ (\S+)  # SPSNR_I
                                        \s+ (\S+) \s+ (\S+) \s+ (\S+)  # CPPPSNR
                                        \s+ (\S+) \s+ (\S+) \s+ (\S+)  # E2EWSPSNR
                                        \s+ (\S+) \s+ (\S+) \s+ (\S+)  # PSNR_VP0
                                        \s+ (\S+) \s+ (\S+) \s+ (\S+) $  # PSNR_VP1
                                        """, log_text, re.M + re.X)
        data = {}
        names = {1: 'Frames', 2: 'Bitrate',
                 3: 'Y-PSNR', 4: 'U-PSNR', 5: 'V-PSNR', 6: 'YUV-PSNR',
                 7: 'Y-SPSNR_NN', 8: 'U-SPSNR_NN', 9: 'V-SPSNR_NN',
                 10: 'Y-WSPSNR', 11: 'U-WSPSNR', 12: 'V-WSPSNR',
                 13: 'Y-SPSNR_I', 14: 'U-SPSNR_I', 15: 'V-SPSNR_I',
                 16: 'Y-CPPSNR', 17: 'U-CPPSNR', 18: 'V-CPPSNR',
                 19: 'Y-E2EWSPSNR', 20: 'U-E2EWSPSNR', 21: 'V-E2EWSPSNR',
                 22: 'Y-PSNR_VP0', 23: 'U-PSNR_VP0', 24: 'V-PSNR_VP0',
                 25: 'Y-PSNR_VP1', 26: 'U-PSNR_VP1', 27: 'V-PSNR_VP1'
                 }

        for i in range(0, len(summaries)):  # iterate through Summary, I, P, B
            data2 = {name: [] for (index, name) in names.items()}
            for (index, name) in names.items():
                data2[name].append(
                    (summaries[i][2], summaries[i][index])
                )
            data[summaries[i][0]] = data2

        return data

    def _parse_temporal_data(self):
        #this function extracts temporal values
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            tempData = re.findall(r"""
                ^POC \s+ (\d+) \s+ .+ \s+ \d+ \s+ . \s+ (.-\D+) ,  # POC, Slice
                \s .+ \) \s+ (\d+) \s+ \S+ \s+  # bitrate
                \[ \S \s (\S+) \s \S+ \s+ \S \s (\S+) \s \S+ \s+ \S \s (\S+) \s \S+ ] \s  # y-, u-, v-PSNR
                \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-SPSNR_NN
                \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-WSPSNR
                \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-SPSNR_I
                \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-CPPPSNR
                \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-E2EWSPSNR
                \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-PSNR_VP0
                \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-PSNR_VP1
                """, log_text, re.M + re.X)

        # Association between index of data in tempData and corresponding
        # output key. Output shape definition is in one place.
        names = {0: 'Frames', 2: 'Bits',
                 3: 'Y-PSNR', 4: 'U-PSNR', 5: 'V-PSNR',
                 6: 'Y-SPSNR_NN', 7: 'U-SPSNR_NN', 8: 'V-SPSNR_NN',
                 9: 'Y-WSPSNR', 10: 'U-WSPSNR', 11: 'V-WSPSNR',
                 12: 'Y-SPSNR_I', 13: 'U-SPSNR_I', 14: 'V-SPSNR_I',
                 15: 'Y-CPPSNR', 16: 'U-CPPSNR', 17: 'V-CPPSNR',
                 18: 'Y-E2EWSPSNR', 19: 'U-E2EWSPSNR', 20: 'V-E2EWSPSNR',
                 21: 'Y-PSNR_VP0', 22: 'U-PSNR_VP0', 23: 'V-PSNR_VP0',
                 24: 'Y-PSNR_VP1', 25: 'U-PSNR_VP1', 26: 'V-PSNR_VP1'
                 }

        # Define output data dict and fill it with parsed values
        data = {name: [] for (index, name) in names.items()}
        for i in range(0, len(tempData)):
            # As referencing to frame produces error, reference to index *i*
            for (index, name) in names.items():
                data[name].append(
                    (i, tempData[i][index])
                )
        return data
