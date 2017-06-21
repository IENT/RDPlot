##################################################################################################
#    This file is part of RDPlot - A gui for creating rd plots based on pyqt and matplotlib
#    <https://git.rwth-aachen.de/IENT-Software/rd-plot-gui>
#    Copyright (C) 2017  Institut fuer Nachrichtentechnik, RWTH Aachen University, GERMANY
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##################################################################################################
import re

from os.path import abspath, join, isdir, isfile, normpath, basename, sep, dirname, splitext
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
        self.additional_params = []

    def _parse_path(self, path):
        """ parses the identifiers for an encoder log out of the
        path of the logfile and the sequence name and qp given in
         the logfile"""
        # set config to path of sim data item
        config = dirname(normpath(path))
        # open log file and parse for sequence name and qp
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            sequence = re.findall(r""" ^Input \s+ File \s+ : \s+ (\S+) $
                                    """, log_text, re.M + re.X)
            qp = re.findall(r""" ^QP \s+ : \s+ (\d+(?:.\d+)?) $
                                  """, log_text, re.M + re.X)
            if not qp:
                qp = re.findall(r"""^QP\s+:\s+(\d+(?:.\d+)?)\s+\(incrementing internal QP at source frame (\d+)\)$""",log_text, re.M)
                qp = '/'.join(list(qp[0]))

        # join all found qps together, that is necessary
        # for SHM
        try:
            qp = " ".join([str(float(q)) for q in qp])
        except ValueError:
            pass

        if qp == "":
            raise SimulationDataItemError
        # set sequence to the sequence name without path and suffix
        # not for
        sequence = splitext(basename(sequence[-1]))[0]

        return sequence, config, qp

    # Properties

    @property
    def tree_identifier_list(self):
        """Builds up the tree in case of more than one (QP) parameter varied in one simulation directory """
        # This is for conformance with rd data written out by older versions of rdplot
        if not hasattr(self, 'additional_params'):
            self.additional_params = []
        return [self.__class__.__name__, self.sequence, self.config] + \
               list(filter(None,['+'.join("{!s}={!r}".format(key,val) for (key,val) in dict((k, self.encoder_config[k]) for k in self.additional_params).items())])) + \
               [self.qp]


    @property
    def data(self):
        # This is for conformance with rd data written out by older versions of rdplot
        if not hasattr(self, 'additional_params'):
            self.additional_params = []
        return [
            (
                [self.sequence, self.config, self.qp],
                {self.__class__.__name__ : {'Temporal': self.temporal_data}}
            ),
            (
                [self.sequence, self.config] +
                list(filter(None,['+'.join("{!s}={!r}".format(key,val) for (key,val) in dict((k, self.encoder_config[k]) for k in self.additional_params).items())])),
                {self.__class__.__name__ : {'Summary': self.summary_data}}
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
    # Order value, used to determine order in which parser are tried.
    parse_order = 10

    def __init__(self, path):
        super().__init__(path)
        self.encoder_config = self._parse_encoder_config()

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

    def _parse_encoder_config(self):
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            lines = log_text.split('\n')
            cleanlist = []
            for one_line in lines:
                if one_line:
                    if 'Non-environment-variable-controlled' in one_line:
                        break
                    if one_line.count(':') == 1:
                        clean_line = one_line.strip(' \n\t\r')
                        clean_line = clean_line.replace(' ', '')
                        cleanlist.append(clean_line)
                    #elif one_line.count(':')>1:
                    # Ignore Multiline stuff for now
                    # TODO: do something smart
                    #else:
                    # Something else happened, do nothing
                    # TODO: do something smart
        parsed_config = dict(item.split(':') for item in cleanlist)
        return parsed_config

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
    # Order value, used to determine order in which parser are tried.
    parse_order = 11

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
    # Order value, used to determine order in which parser are tried.
    parse_order = 20

    def __init__(self, path):
        super().__init__(path)
        self.encoder_config = self._parse_encoder_config()

    @classmethod
    def can_parse_file(cls, path):
        return cls._enc_log_file_matches_re_pattern(
            path,
            r'Y-PSNR_(?:DYN_)?VP0',
        ) #Y-PSNR_DYN_VP0

    def _parse_encoder_config(self):
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            lines = log_text.split('\n')
            cleanlist = []
            for one_line in lines:
                if one_line:
                    if '-----360 video parameters----' in one_line:
                        break
                    if one_line.count(':') == 1:
                        clean_line = one_line.strip(' \n\t\r')
                        clean_line = clean_line.replace(' ', '')
                        cleanlist.append(clean_line)
                    #elif one_line.count(':')>1:
                    # Ignore Multiline stuff for now
                    # TODO: do something smart
                    #else:
                    # Something else happened, do nothing
                    # TODO: do something smart
        parsed_config = dict(item.split(':') for item in cleanlist)

        # parse 360 rotation parameter
        m = re.search('Rotation in 1/100 degrees:\s+\(yaw:(\d+)\s+pitch:(\d+)\s+roll:(\d+)\)', log_text)
        if m:
            yaw = m.group(1)
            pitch = m.group(2)
            roll = m.group(3)
            parsed_config['SVideoRotation'] = 'Y%sP%sR%s' % (yaw, pitch, roll)

        return parsed_config

    def _parse_summary_data(self):

        if self._enc_log_file_matches_re_pattern(self.path, r'Y-PSNR_VP0'):
            # 360Lib version < 3.0
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

        else:
            # 360Lib version  3.0
            with open(self.path, 'r') as log_file:
                log_text = log_file.read()  # reads the whole text file
                summaries = re.findall(r""" ^(\S+) .+ $ \s .+ $
                                            \s+ (\d+) \s+ \D \s+ (\S+)  # Total Frames, Bitrate
                                            \s+ (\S+) \s+ (\S+) \s+ (\S+) \s+ (\S+)  # y-, u-, v-, yuv-PSNR
                                            \s+ (\S+) \s+ (\S+) \s+ (\S+)  # WSPSNR
                                            \s+ (\S+) \s+ (\S+) \s+ (\S+)  # E2ESPSNR_NN
                                            \s+ (\S+) \s+ (\S+) \s+ (\S+)  # E2ESPSNR_I
                                            \s+ (\S+) \s+ (\S+) \s+ (\S+)  # E2ECPPPSNR
                                            \s+ (\S+) \s+ (\S+) \s+ (\S+)  # E2EWSPSNR
                                            \s+ (\S+) \s+ (\S+) \s+ (\S+)  # PSNR_DYN_VP0
                                            \s+ (\S+) \s+ (\S+) \s+ (\S+)  # PSNR_DYN_VP1
                                            \s+ (\S+) \s+ (\S+) \s+ (\S+)  # CFSPSNR_NN
                                            \s+ (\S+) \s+ (\S+) \s+ (\S+)  # CFSPSNR_I
                                            \s+ (\S+) \s+ (\S+) \s+ (\S+) \s+ $  # CFCPPPSNR
                                            """, log_text, re.M + re.X)

            data = {}
            names = {1: 'Frames', 2: 'Bitrate',
                     3: 'Y-PSNR', 4: 'U-PSNR', 5: 'V-PSNR', 6: 'YUV-PSNR',
                     7: 'Y-WSPSNR', 8: 'U-WSPSNR', 9: 'V-WSPSNR',
                     10: 'Y-E2ESPSNR_NN', 11: 'U-E2ESPSNR_NN', 12: 'V-E2ESPSNR_NN',
                     13: 'Y-E2ESPSNR_I', 14: 'U-E2ESPSNR_I', 15: 'V-E2ESPSNR_I',
                     16: 'Y-E2ECPPPSNR', 17: 'U-E2ECPPPSNR', 18: 'V-E2ECPPPSNR',
                     19: 'Y-E2EWSPSNR', 20: 'U-E2EWSPSNR', 21: 'V-E2EWSPSNR',
                     22: 'Y-PSNR_DYN_VP0', 23: 'U-PSNR_DYN_VP0', 24: 'V-PSNR_DYN_VP0',
                     25: 'Y-PSNR_DYN_VP1', 26: 'U-PSNR_DYN_VP1', 27: 'V-PSNR_DYN_VP1',
                     28: 'Y-CFSPSNR_NN', 29: 'U-CFSPSNR_NN', 30: 'V-CFSPSNR_NN',
                     31: 'Y-CFSPSNR_I', 32: 'U-CFSPSNR_I', 33: 'V-CFSPSNR_I',
                     34: 'Y-CFCPPPSNR', 35: 'U-CFCPPPSNR', 36: 'V-CFCPPPSNR'

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
    # Order value, used to determine order in which parser are tried.
    parse_order = 21

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

            # add the addtion of layers 1 and two in rate. PSNR values are taken from Layer one
            # TODO make this nice one day
            layerstring = 'layer 1 + 2'
            #data2[layerstring] = {}
            data4 = {}
            bitrate = 0
            for layer in range(0, layer_quantity):
                if summaries[layer_quantity * it + layer_quantity - 1][2] != '-nan':
                    bitrate += float(summaries[layer_quantity * it + layer][2])
            for (index, name) in names.items():
                data4[name] = []
                if summaries[layer_quantity * it + layer_quantity - 1][2] == 'nan':
                    data4[name].append((float(0), float(0)))
                else:
                    data4[name].append(
                        (bitrate, float(summaries[layer_quantity * it + layer_quantity - 1][index])))
            data2[layerstring] = data4

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

#
# class EncLogHM360LibOld(AbstractEncLog):
#     @classmethod
#     def can_parse_file(cls, path):
#         return cls._enc_log_file_matches_re_pattern(
#             path,
#             r'^-----360 \s video \s parameters----',
#         )
#
#     def _parse_summary_data(self):
#         with open(self.path, 'r') as log_file:
#             log_text = log_file.read()  # reads the whole text file
#             summaries = re.findall(r""" ^(\S+) .+ $ \s .+ $
#                                         \s+ (\d+) \s+ \D \s+ (\S+)  # Total Frames, Bitrate
#                                         \s+ (\S+) \s+ (\S+) \s+ (\S+) \s+ (\S+)  # y-, u-, v-, yuv-PSNR
#                                         \s+ (\S+) \s+ (\S+) \s+ (\S+)  # WSPSNR
#                                         \s+ (\S+) \s+ (\S+) \s+ (\S+)  # CPPPSNR
#                                         \s+ (\S+) \s+ (\S+) \s+ (\S+) \s $  # E2EWSPSNR
#                                         """, log_text, re.M + re.X)
#         data = {}
#         names = {1: 'Frames', 2: 'Bitrate', 3: 'Y-PSNR', 4: 'U-PSNR',
#                  5: 'V-PSNR', 6: 'YUV-PSNR', 7: 'Y-WSPSNR', 8: 'U-WSPSNR',
#                  9: 'V-WSPSNR', 10: 'Y-CPPSNR', 11: 'U-CPPSNR', 12: 'V-CPPSNR',
#                  13: 'Y-E2EWSPSNR', 14: 'U-E2EWSPSNR', 15: 'V-E2EWSPSNR'}
#
#         for i in range(0, len(summaries)):  # iterate through Summary, I, P, B
#             data2 = {name: [] for (index, name) in names.items()}
#             for (index, name) in names.items():
#                 data2[name].append(
#                     (float(summaries[i][2]), float(summaries[i][index]))
#                 )
#             data[summaries[i][0]] = data2
#
#         # viewport = re.findall(r""" ^\s+ (\d+) \s+ \D \s+ (\d+)  # total frames, viewport
#         #                            \s+ (\S+) \s+ (\S+) \s+ (\S+) \s+ (\S+)  # y-,u-,v-, yuv-PSNR
#         #                            \s+ (\S+) \s+ (\S+) \s+ (\S+) \s+ (\S+)$  # y-,u-,v-, yuv-MSE
#         #                             """, log_text, re.M + re.X)
#         #
#         # viewportNames = {0: 'Frames', 1: 'Viewport', 2: 'Y-PSNR', 3: 'U-PSNR',
#         #          4: 'V-PSNR', 5: 'YUV-PSNR', 6: 'Y-MSE', 7: 'U-MSE',
#         #          8: 'V-MSE', 9: 'Y-MSE'}
#
#         return data
#
#     def _parse_temporal_data(self):
#         # this function extracts temporal values
#         with open(self.path, 'r') as log_file:
#             log_text = log_file.read()  # reads the whole text file
#             temp_data = re.findall(r"""
#                 ^POC \s+ (\d+) \s+ .+ \s+ \d+ \s+ . \s+ (.-\D+) ,  # POC, Slice
#                 \s .+ \) \s+ (\d+) \s+ \S+ \s+  # bits
#                 \[ \S \s (\S+) \s \S+ \s+ \S \s (\S+) \s \S+ \s+ \S \s (\S+) \s \S+ ] \s  # y-, u-, v-PSNR
#                 \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-WSPSNR
#                 \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-CPPPSNR
#                 \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-E2EWSPSNR
#                 """, log_text, re.M + re.X)
#
#         # Association between index of data in temp_data and corresponding
#         # output key. Output shape definition is in one place.
#         names = {0: 'Frames', 2: 'Bits',
#                  3: 'Y-PSNR', 4: 'U-PSNR', 5: 'V-PSNR',
#                  6: 'Y-WSPSNR', 7: 'U-WSPSNR', 8: 'V-WSPSNR',
#                  9: 'Y-CPPSNR', 10: 'U-CPPSNR', 11: 'V-CPPSNR',
#                  12: 'Y-E2EWSPSNR', 13: 'U-E2EWSPSNR', 14: 'V-E2EWSPSNR',
#                  }
#
#         # Define output data dict and fill it with parsed values
#         data = {name: [] for (index, name) in names.items()}
#         for i in range(0, len(temp_data)):
#             # As referencing to frame produces error, reference to index *i*
#             for (index, name) in names.items():
#                 data[name].append(
#                     (i, temp_data[i][index])
#                 )
#         return data
