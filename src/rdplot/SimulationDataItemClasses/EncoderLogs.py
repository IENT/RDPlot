import re

from os.path import abspath, join, isdir, isfile, normpath, basename, sep, dirname
from abc import ABCMeta

from SimulationDataItem import (AbstractSimulationDataItem,
                                SimulationDataItemError)


class AbstractEncLog(AbstractSimulationDataItem):
    def __init__(self, path):
        super().__init__(path)

        # Parse file path and set additional identifiers
        # self.logType = self._get_Type(path)
        self.sequence, self.config, self.qp = self._parse_path(self.path)

        # Dictionaries holding the parsed values
        self.summary_data = self._parse_summary_data()
        self.temporal_data = self._parse_temporal_data()

    def _parse_path(self, path):
        try:
            # Assumes structure of .../<simulation_directory>/log/<basename>
            filename = basename(path)
        except IndexError:
            raise SimulationDataItemError(
                "Path {} can not be splitted into directories and filename"
                .format(filename, path)
            )

        try:
            separator = '-'
            filename_splitted = filename.split('_QP')[0].split(separator)
            sequence = filename_splitted[-1]
            config = separator.join(filename_splitted[0: -2])
        except IndexError:
            raise SimulationDataItemError((
                "Filename {} can not be splitted into config until '{}' and"
                " sequence between last '{}' and '_QP'"
            ).format(filename, separator, separator))

        # prepend simulation directory to config
        config = dirname(normpath(path)) + config
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            qp = re.findall(r""" ^QP \s+ : \s+ (\d+.\d+) $
                                  """, log_text, re.M + re.X)
        # join all found qps together, that is necessary
        # for SHM
        qp = " ".join([str(q) for q in qp])
        if qp == "":
            raise SimulationDataItemError

        return sequence, config, qp

    # Properties

    @property
    def tree_identifier_list(self):
        return [self.__class__.__name__, self.sequence, self.config, self.qp]

    @property
    def data(self):
        return [
            (
                [self.sequence, self.config, self.qp],
                {'Temporal': self.temporal_data}
            ),
            (
                [self.sequence, self.config],
                {'Summary': self.summary_data}
            ),
        ]

    # Non-abstract Helper Functions
    @classmethod
    def _enc_log_file_matches_re_pattern(cls, path, pattern):
        """"""
        if path.endswith("enc.log"):
            return cls._is_file_text_matching_re_pattern(path, pattern)
        return False


class EncLogHM(AbstractEncLog):
    @classmethod
    def can_parse_file(cls, path):
        return cls._enc_log_file_matches_re_pattern(
            path,
            r'^HM \s software'
        )

    def _parse_summary_data(self):
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            # catch summary line
            summaries = re.findall(r""" ^(\w*)-*.*$
                           \s* # catch newline and space
                           (.*)\| # catch phrase Total Frames / I / P / B
                           (\s+\S+)(\s+\S+)(\s+\S+)(\s+\S+)(\s+\S+)# catch rest of the line
                           \s* # catch newline and space
                           (\d+\s+)\w # catch frame number
                           (\s+\d+\.\d+)(\s+\d+\.\d+)(\s+\d+\.\d+)(\s+\d+\.\d+)(\s+\d+\.\d+) # catch the fractional number (rate, PSNRs)
                      """, log_text, re.M + re.X)

        data = {}
        for summary in summaries:
            summary_type = summary[0]
            # Create upon first access
            if summary_type not in data:
                data[summary_type] = {}
            names = summary[1:7]
            vals = summary[7:]

            names = [name.strip() for name in names]  # remove leading and trailing space
            vals = [float(val) for val in vals]  # convert to numbers

            name_val_dict = dict(zip(names, vals))  # pack both together in a dict
            # print(summary_type)

            name_rate = 'Bitrate'
            names.remove('Bitrate')

            # now pack everything together
            for name in names:
                if name not in data[summary_type]:  # create upon first access
                    data[summary_type][name] = []
                # Reference all data to *self.qp*
                data[summary_type][name].append(
                    (name_val_dict[name_rate], name_val_dict[name])
                )
        return data

    def _parse_temporal_data(self):
        # this function extracts temporal values
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file

        temp_data = re.findall(r"""
            ^POC \s+ (\d+) \s+ .+ \s+ \d+ \s+ . \s+ (.-\D+) ,  #Slice
            \s .+ \) \s+ (\d+) \s+ (.+) \s+ \[ (\D+) \s+ (\d+.\d+) \s+ #Y PSNR
            \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ # U PSNR
            \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ # v PSNR
            """, log_text, re.M + re.X)

        # Association between index of data in temp_data and corresponding
        # output key. Output shape definition is in one place.
        names = {0: 'Frames', 2: 'Bits', 5: 'Y-PSNR', 7: 'U-PSNR',
                 9: 'V-PSNR'}

        # Define output data dict and fill it with parsed values
        data = {name: [] for (index, name) in names.items()}
        for i in range(0, len(temp_data)):
            # As referencing to frame produces error, reference to index *i*
            for (index, name) in names.items():
                data[name].append(
                    (i, temp_data[i][index])
                )
        return data


class EncLogHM14(EncLogHM):
    @classmethod
    def can_parse_file(cls, path):
        return cls._enc_log_file_matches_re_pattern(
            path,
            r'^HM \s software: \s Encoder \s Version \s \[14'
        )

    def _parse_summary_data(self):
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            # catch summary line
            summaries = re.findall(r""" ^(\w*)-*.*$
                               \s* # catch newline and space
                               (.*)\| # catch phrase Total Frames / I / P / B
                               (\s+\S+)(\s+\S+)(\s+\S+)(\s+\S+)# catch rest of the line
                               \s* # catch newline and space
                               (\d+\s+)\w # catch frame number
                               (\s+\d+\.\d+)(\s+\d+\.\d+)(\s+\d+\.\d+)(\s+\d+\.\d+) # catch the fractional number (rate, PSNRs)
                          """, log_text, re.M + re.X)

        data = {}
        for summary in summaries:
            summary_type = summary[0]
            # Create upon first access
            if summary_type not in data:
                data[summary_type] = {}
            names = summary[1:6]
            vals = summary[6:]

            names = [name.strip() for name in names]  # remove leading and trailing space
            vals = [float(val) for val in vals]  # convert to numbers

            name_val_dict = dict(zip(names, vals))  # pack both together in a dict
            # print(summary_type)

            name_rate = 'Bitrate'
            names.remove('Bitrate')

            # now pack everything together
            for name in names:
                if name not in data[summary_type]:  # create upon first access
                    data[summary_type][name] = []
                # Reference all data to *self.qp*
                data[summary_type][name].append(
                    (name_val_dict[name_rate], name_val_dict[name])
                )
        return data


class EncLogHM360Lib(AbstractEncLog):
    @classmethod
    def can_parse_file(cls, path):
        return cls._enc_log_file_matches_re_pattern(
            path,
            r'Y-PSNR_VP0',
        )

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
                    (float(summaries[i][2]), float(summaries[i][index]))
                )
            data[summaries[i][0]] = data2

        return data

    def _parse_temporal_data(self):
        # this function extracts temporal values
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            temp_data = re.findall(r"""
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

        # Association between index of data in temp_data and corresponding
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
        for i in range(0, len(temp_data)):
            # As referencing to frame produces error, reference to index *i*
            for (index, name) in names.items():
                data[name].append(
                    (i, temp_data[i][index])
                )
        return data


class EncLogSHM(AbstractEncLog):
    @classmethod
    def can_parse_file(cls, path):
        return cls._enc_log_file_matches_re_pattern(
            path,
            r'^SHM \s software'
        )

    def _parse_summary_data(self):
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            summaries = re.findall(r"""
                        ^\s+ L (\d+) \s+ (\d+) \s+ \D \s+ # the next is bitrate
                        (\S+) \s+ (\S+) \s+ (\S+) \s+ (\S+) \s+ (\S+)
                        """, log_text, re.M + re.X)

        data = {}
        layer_quantity = int(len(summaries) / 4)
        header_names = ['SUMMARY', 'I', 'P', 'B']
        names = {1: 'Frames', 2: 'Bitrate', 3: 'Y-PSNR', 4: 'U-PSNR',
                 5: 'V-PSNR', 6: 'YUV-PSNR'}

        for it in range(0, 4):  # iterate through Summary, I, P, B
            data2 = {}
            for layer in range(0, layer_quantity):  # iterate through layers
                layerstring = 'layer ' + str(layer)
                data2[layerstring] = {}
                data3 = {}
                bitrate = summaries[layer_quantity * it + layer][2]
                for (index, name) in names.items():
                    # convert string '-nan' to int 0 if necessary
                    data3[name] = []
                    if isinstance(bitrate, str) and (bitrate == '-nan'):
                        data3[name].append(
                            (float(0), float(0))
                        )
                    else:
                        data3[name].append(
                            (float(bitrate), float(summaries[layer_quantity * it + layer][index]))
                        )
                data2[layerstring] = data3
            data[header_names[it]] = data2
        return data

    def _parse_temporal_data(self):
        # this function extracts temporal values
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            temp_data = re.findall(r"""
                                ^POC \s+ (\d+) .+? : \s+ (\d+) .+ (\D-\D+) \s \D+,  #Slice
                                .+ \) \s+ (\d+) \s+ (.+) \s+ \[ (\D+) \s+ (\d+.\d+) \s+ #Y PSNR
                                \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ # U PSNR
                                \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ # v PSNR
                                """, log_text, re.M + re.X)

        # Association between index of data in temp_data and corresponding
        # output key. Output shape definition is in one place.
        names = {0: 'Frames', 3: 'Bits', 6: 'Y-PSNR', 8: 'U-PSNR',
                 10: 'V-PSNR'}

        layer_quantity = int(max(temp_data[i][1] for i in range(0, len(temp_data)))) + 1
        layer_quantity = int(layer_quantity)
        data = {}
        for layer in range(0, layer_quantity):  # iterate through layers
            data2 = {name: [] for (index, name) in names.items()}
            for j in range(0, int(len(temp_data)/layer_quantity)):  # iterate through frames (POCS)
                for (index, name) in names.items():
                    data2[name].append(
                        (j, temp_data[layer_quantity*j+layer][index])
                    )
            layerstring = 'layer ' + str(layer)
            data[layerstring] = data2
        return data


class EncLogHM360LibOld(AbstractEncLog):
    @classmethod
    def can_parse_file(cls, path):
        return cls._enc_log_file_matches_re_pattern(
            path,
            r'^-----360 \s video \s parameters----',
        )

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
                    (float(summaries[i][2]), float(summaries[i][index]))
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
