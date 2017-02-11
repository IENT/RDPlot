from model import (SimDataItem, SimDataItemParserError)

from os.path import (basename, sep, normpath)
import re


class EncLogHM360LibOld(SimDataItem):
    def __init__(self, path):
        super().__init__(path)

    def _parse_path(self, path):
        try:
            # Assumes structure of .../<simulation_directory>/log/<basename>
            directories = normpath(path).split(sep)[0: -2]
            filename = basename(path)
        except IndexError:
            raise SimDataItemParserError(
                "Path {} can not be splitted into directories and filename"
                .format(filename, path)
            )

        try:
            seperator = '-'
            filename_splitted = filename.split('_QP')[0].split(seperator)
            sequence = filename_splitted[-1]
            config = seperator.join(filename_splitted[0: -2])
        except IndexError:
            raise SimDataItemParserError((
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
                                        \s+ (\S+) \s+ (\S+) \s+ (\S+)  # WSPSNR
                                        \s+ (\S+) \s+ (\S+) \s+ (\S+)  # CPPPSNR
                                        \s+ (\S+) \s+ (\S+) \s+ (\S+) \s $  # E2EWSPSNR
                                        """, log_text, re.M + re.X)
        data = {}
        names = {1: 'Frames', 2: 'Bitrate', 3: 'Y-PSNR', 4: 'U-PSNR',
                 5: 'V-PSNR', 6: 'YUV-PSNR', 7: 'Y-WSPSNR', 8: 'U-WSPSNR',
                 9: 'V-WSPSNR', 10: 'Y-CPPSNR', 11: 'U-CPPSNR', 12: 'V-CPPSNR',
                 13: 'Y-E2EWSPSNR', 14: 'U-E2EWSPSNR', 15: 'V-E2EWSPSNR'}

        for i in range(0, len(summaries)):  # iterate through Summary, I, P, B
            data2 = {name: [] for (index, name) in names.items()}
            for (index, name) in names.items():
                data2[name].append(
                    (summaries[i][2], summaries[i][index])
                )
            data[summaries[i][0]] = data2

        # viewport = re.findall(r""" ^\s+ (\d+) \s+ \D \s+ (\d+)  # total frames, viewport
        #                            \s+ (\S+) \s+ (\S+) \s+ (\S+) \s+ (\S+)  # y-,u-,v-, yuv-PSNR
        #                            \s+ (\S+) \s+ (\S+) \s+ (\S+) \s+ (\S+)$  # y-,u-,v-, yuv-MSE
        #                             """, log_text, re.M + re.X)
        #
        # viewportNames = {0: 'Frames', 1: 'Viewport', 2: 'Y-PSNR', 3: 'U-PSNR',
        #          4: 'V-PSNR', 5: 'YUV-PSNR', 6: 'Y-MSE', 7: 'U-MSE',
        #          8: 'V-MSE', 9: 'Y-MSE'}

        return data

    def _parse_temporal_data(self):
        # this function extracts temporal values
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            temp_data = re.findall(r"""
                ^POC \s+ (\d+) \s+ .+ \s+ \d+ \s+ . \s+ (.-\D+) ,  # POC, Slice
                \s .+ \) \s+ (\d+) \s+ \S+ \s+  # bits
                \[ \S \s (\S+) \s \S+ \s+ \S \s (\S+) \s \S+ \s+ \S \s (\S+) \s \S+ ] \s  # y-, u-, v-PSNR
                \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-WSPSNR
                \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-CPPPSNR
                \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-E2EWSPSNR
                """, log_text, re.M + re.X)

        # Association between index of data in temp_data and corresponding
        # output key. Output shape definition is in one place.
        names = {0: 'Frames', 2: 'Bits',
                 3: 'Y-PSNR', 4: 'U-PSNR', 5: 'V-PSNR',
                 6: 'Y-WSPSNR', 7: 'U-WSPSNR', 8: 'V-WSPSNR',
                 9: 'Y-CPPSNR', 10: 'U-CPPSNR', 11: 'V-CPPSNR',
                 12: 'Y-E2EWSPSNR', 13: 'U-E2EWSPSNR', 14: 'V-E2EWSPSNR',
                 }

        # Define output data dict and fill it with parsed values
        data = {name: [] for (index, name) in names.items()}
        for i in range(0, len(temp_data)):
            # As referencing to frame produces error, reference to index *i*
            for (index, name) in names.items():
                data[name].append(
                    (i, temp_data[i][index])
                )
        return data
