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
from abc import abstractmethod
from collections import defaultdict
from os.path import normpath, basename, dirname, splitext, split

from rdplot.SimulationDataItem import (AbstractSimulationDataItem)


class AbstractEncLog(AbstractSimulationDataItem):
    def __init__(self, path):
        super().__init__(path)

        # Parse file path and set additional identifiers
        # self.logType = self._get_Type(path)
        self.sequence, self.config = self._parse_path(self.path)

        # Dictionaries holding the parsed values
        self.summary_data = self._parse_summary_data()
        self.temporal_data = self._parse_temporal_data()
        self.additional_params = []

        self.log_config = self._parse_config()

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

        # set sequence to the sequence name without path and suffix
        # not for
        sequence = splitext(basename(sequence[-1]))[0]

        return sequence, config

    @staticmethod
    def _get_label(keys):
        """
        :param keys: Variable/Path for which to get the labels
        :return: tuple of labels: (x-axis label, y-axis label)
        """
        # create all the labels with dictionaries. The leaves are tuples of x, y-labels
        labels = {}
        labels['Summary'] = {}
        labels['Summary']['B'] = labels['Summary']['B Slices'] = labels['Summary']['B']['layer 0'] = \
            labels['Summary']['B']['layer 1'] = labels['Summary']['B']['layer 1 + 2'] = defaultdict(
            lambda: ('kbps', 'dB'))
        labels['Summary']['I'] = labels['Summary']['I Slices'] = labels['Summary']['I']['layer 0'] = \
            labels['Summary']['I']['layer 1'] = labels['Summary']['I']['layer 1 + 2'] = defaultdict(
            lambda: ('kbps', 'dB'))
        labels['Summary']['P'] = labels['Summary']['P Slices'] = labels['Summary']['P']['layer 0'] = \
            labels['Summary']['P']['layer 1'] = labels['Summary']['P']['layer 1 + 2'] = defaultdict(
            lambda: ('kbps', 'dB'))
        labels['Summary']['SUMMARY'] = \
            labels['Summary']['SUMMARY']['layer 0'] = \
            labels['Summary']['SUMMARY']['layer 1'] = \
            labels['Summary']['SUMMARY']['layer 1 + 2'] = \
            labels['Summary']['PSNR1'] = \
            labels['Summary']['PSNR2'] = \
            labels['Summary']['PSNR3'] = \
            labels['Summary']['PSNR4'] = \
            defaultdict(lambda: ('kbps', 'dB'))

        labels['Summary']['B']['Bitrate'] = labels['Summary']['I']['Bitrate'] = labels['Summary']['P']['Bitrate'] = \
            labels['Summary']['SUMMARY']['Bitrate'] = ('kbps', 'bits')
        labels['Summary']['B']['Frames'] = labels['Summary']['B']['Total Frames'] = ('kbps', 'Frames')
        labels['Summary']['I']['Frames'] = labels['Summary']['I']['Total Frames'] = ('kbps', 'Frames')
        labels['Summary']['P']['Frames'] = labels['Summary']['P']['Total Frames'] = ('kbps', 'Frames')
        labels['Summary']['SUMMARY']['Frames'] = labels['Summary']['SUMMARY']['Total Frames'] = ('kbps', 'Frames')
        labels['Summary']['SUMMARY']['Total Time'] = ('kbps', 'sec')
        labels['Summary']['SUMMARY']['HM Major Version'] = labels['Summary']['SUMMARY']['HM Minor Version'] = \
            labels['Summary']['SUMMARY']['360Lib Version'] = ('', 'sec')

        labels['Temporal'] = labels['Temporal']['layer 0'] = labels['Temporal']['layer 1'] = defaultdict(
            lambda: ('Frame', 'dB'))
        labels['Temporal']['Bits'] = ('Frame', 'bits')
        labels['Temporal']['Frames'] = ('Frame', 'POC')
        labels['Temporal']['ET'] = ('Frame', 'sec')
        label = labels
        # return needed label with keys

        for idx in keys[1:]:
            if isinstance(label[idx], dict):
                label = label[idx]
            else:
                label = label[idx]
                return label

    # Properties

    @property
    def tree_identifier_list(self):
        """Builds up the tree in case of more than one (QP) parameter varied in one simulation directory """
        # This is for conformance with rd data written out by older versions of rdplot
        if not hasattr(self, 'additional_params'):
            self.additional_params = []
        try:
            l1 = list(zip(self.additional_params, [self.log_config[i] for i in self.additional_params]))
            l1 = list(map(lambda x: '='.join(x), l1))
            return [self.__class__.__name__, self.sequence, self.config] + l1
        except:
            # MESSAGEBOX
            self.additional_params = ['QP']
            return [self.__class__.__name__, self.sequence, self.config]

    @abstractmethod
    def _parse_config(self):
        """Method which parses log file to get config (QP, other parameters).
        Abstract, needs to be implemented by encoder log parsers
        :return:
        """
        pass

    @property
    def data(self):
        # This is for conformance with rd data written out by older versions of rdplot
        if not hasattr(self, 'additional_params'):
            self.additional_params = []
        l1 = list(zip(self.additional_params, [self.log_config[i] for i in self.additional_params]))
        l1 = list(map(lambda x: '='.join(x), l1))
        return [
            (
                [self.sequence, self.config] + l1[0:len(l1)],
                {self.__class__.__name__: {'Temporal': self.temporal_data}}
            ),
            (
                [self.sequence, self.config] + l1[0:len(l1) - 1],
                {self.__class__.__name__: {'Summary': self.summary_data}}
            ),
        ]

    # Abstract Methods/Properties
    @classmethod
    @abstractmethod
    def can_parse_file(cls, path):
        """Check, if the file at *path* can be parsed by the class. The class
        can can for example check, if the file name or the file extension
        matches a certain pattern, or inspect the contents of the file. Note,
        that the first class which returns ``True`` with respect to a file on
        this method, will be be used to parse the file. Thus, classes should
        implement this method as specific as possible.

        :param path:  path to file
        :type path: :class: `String`

        :rtype: :class: `Bool`
        """
        pass

    # Non-abstract Helper Functions
    @classmethod
    def _enc_log_file_matches_re_pattern(cls, path, pattern):
        """"""
        if path.endswith("enc.log"):
            return cls._is_file_text_matching_re_pattern(path, pattern)
        return False

    @abstractmethod
    def _parse_summary_data(self):
        """
        Method which parses the summary data of a simulation. I.e. summaries for All, Intra, P and B Slices
        :return:
        """
        pass

    def _parse_temporal_data(self):
        """
        Method which parses the temporal data of a simulation. I.e. rate over poc, quality over poc ...
        :return:
        """
        pass


class EncLogHM(AbstractEncLog):
    # Order value, used to determine order in which parser are tried.
    parse_order = 10

    @classmethod
    def can_parse_file(cls, path):
        matches_class = cls._enc_log_file_matches_re_pattern(path, r'^HM \s software')
        is_finished = cls._enc_log_file_matches_re_pattern(path, 'Total\ Time')
        if is_finished is False and matches_class is True:
            # In case an enc.log file has not a Total Time mark it is very likely that the file is erroneous.
            # TODO: Inform user with a dialog window
            print("Warning: The file" + path + " might be erroneous.")
        return matches_class and is_finished

    def _parse_summary_data(self):
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file

            hm_match = re.search(r'HM software: Encoder Version \[([a-zA-Z-]+)?([0-9]+)\.([0-9]+)', log_text)
            hm_major_version = hm_match.group(2)
            hm_minor_version = hm_match.group(3)

            if hm_major_version == '14':  # HM 14 does not write out average YUV-PSNR
                # catch summary line
                summaries = re.findall(r""" ^(\w*)-*.*$
                                   \s* # catch newline and space
                                   (.*)\| # catch phrase Total Frames / I / P / B
                                   (\s+\S+)(\s+\S+)(\s+\S+)(\s+\S+)# catch rest of the line
                                   \s* # catch newline and space
                                   (\d+\s+)\w # catch frame number (integer)
                                   (\s+\d+\.\d+)(\s+\d+\.\d+)(\s+\d+\.\d+)(\s+\d+\.\d+) # other numbers (rate, PSNRs)
                              """, log_text, re.M + re.X)
                total_time = re.findall(r""" ^\s*Total\s+Time.\s+(\d+.\d+)
                               """, log_text, re.M + re.X)
            else:
                # catch summary line
                summaries = re.findall(r""" ^(\w*)-*.*$
                               \s* # catch newline and space
                               (.*)\| # catch phrase Total Frames / I / P / B
                               (\s+\S+)(\s+\S+)(\s+\S+)(\s+\S+)(\s+\S+)# catch rest of the line
                               \s* # catch newline and space
                               (\d+\s+)\w # catch frame number (integer)
                               (\s+\d+\.\d+)(\s+\d+\.\d+)(\s+\d+\.\d+)(\s+\d+\.\d+)(\s+\d+\.\d+)# others (rate, PSNRs)
                          """, log_text, re.M + re.X)
                total_time = re.findall(r""" ^\s*Total\s+Time.\s+(\d+.\d+)
                               """, log_text, re.M + re.X)
        data = {}
        for summary in summaries:
            summary_type = summary[0]
            # Create upon first access
            if summary_type not in data:
                data[summary_type] = {}

            # remove first element, we need an even number of elements. then split into two list, values and names
            # and pack them together
            summary = summary[1:]
            names = summary[:len(summary) // 2]
            vals = summary[len(summary) // 2:]

            names = [name.strip() for name in names]  # remove leading and trailing space
            vals = [float(val) for val in vals]  # convert to numbers

            name_val_dict = dict(zip(names, vals))  # pack both together in a dict
            # print(summary_type)

            name_rate = 'Bitrate'
            if summary_type == 'SUMMARY':
                bitrate = float(vals[names.index(name_rate)])
            names.remove(name_rate)

            # now pack everything together
            for name in names:
                if name not in data[summary_type]:  # create upon first access
                    data[summary_type][name] = []
                # Reference all data to *self.qp*
                data[summary_type][name].append(
                    (name_val_dict[name_rate], name_val_dict[name])
                )
        # data['Total Time'] = total_time[0]
        data['SUMMARY']['Total Time'] = [(bitrate, float(total_time[0]))]
        data['SUMMARY']['HM Major Version'] = [(bitrate, int(hm_major_version))]
        data['SUMMARY']['HM Minor Version'] = [(bitrate, int(hm_minor_version))]
        return data

    def _parse_config(self):
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            lines = log_text.split('\n')
            cleanlist = []
            # some of the configs should not be interpreted as parameters
            # those are removed from the cleanlist
            param_not_considered = ['RealFormat', 'Warning', 'InternalFormat', 'Byteswrittentofile', 'Frameindex',
                                    'TotalTime', 'HMsoftware']
            for one_line in lines:
                if one_line:
                    if 'Non-environment-variable-controlled' in one_line:
                        break
                    if one_line.count(':') == 1:
                        clean_line = one_line.strip(' \n\t\r')
                        clean_line = re.sub('\s+', '', clean_line)
                        if not any(re.search(param, clean_line) for param in param_not_considered):
                            cleanlist.append(clean_line)
                    elif one_line.count(':') > 1:
                        if re.search('\w+ \s+ \w+ \s+ \w+ \s+ :\s+ \( \w+ : \d+ , \s+ \w+ : \d+ \)', one_line, re.X):
                            clean_line = re.findall('\w+ \s+ \w+ \s+ \w+ \s+ :\s+ \( \w+ : \d+ , \s+ \w+ : \d+ \)',
                                                    one_line, re.X)
                        else:
                            clean_line = re.findall('\w+ : \d+ | \w+ : \s+ \w+ = \d+', one_line, re.X)
                        for clean_item in clean_line:
                            if not any(re.search(param, clean_item) for param in param_not_considered):
                                cleanlist.append(clean_item)

        parsed_config = dict(item.split(':', maxsplit=1) for item in cleanlist)
        self.qp = parsed_config['QP']
        return parsed_config

    def _parse_temporal_data(self):
        # this function extracts temporal values
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file

        temp_data = re.findall(r"""
            ^POC \s+ (\d+) \s+ .+ \s+ \d+ \s+ . \s+ (.-\D+) ,  #Slice
            \s .+ \) \s+ (\d+) \s+ (.+) \s+ #bits
            \[ (\D+) \s+ (\d+.\d+) \s+ #Y PSNR
            \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ # U PSNR
            \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ \D+ . # V PSNR
            \s+ \[ (\D+) \s+ (\d+) \s+# Encoding time
            """, log_text, re.M + re.X)

        # Association between index of data in temp_data and corresponding
        # output key. Output shape definition is in one place.
        names = {0: 'Frames', 2: 'Bits', 5: 'Y-PSNR', 7: 'U-PSNR',
                 9: 'V-PSNR', 11: 'ET'}

        # Define output data dict and fill it with parsed values
        data = {name: [] for (index, name) in names.items()}
        for i in range(0, len(temp_data)):
            # As referencing to frame produces error, reference to index *i*
            for (index, name) in names.items():
                data[name].append(
                    (i, temp_data[i][index])
                )
        return data


class EncLogHM360Lib(AbstractEncLog):
    # Order value, used to determine order in which parser are tried.
    parse_order = 20

    @classmethod
    def can_parse_file(cls, path):
        matches_class = cls._enc_log_file_matches_re_pattern(path, r'Y-PSNR_(?:DYN_)?VP0')
        is_finished = cls._enc_log_file_matches_re_pattern(path, 'Total\ Time')
        return matches_class and is_finished

    def _parse_config(self):
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            lines = log_text.split('\n')
            cleanlist = []
            # some of the configs should not be interpreted as parameters
            # those are removed from the cleanlist
            param_not_considered = ['RealFormat', 'Warning', 'InternalFormat', 'Byteswrittentofile', 'Frameindex',
                                    'TotalTime', 'HMsoftware']
            for one_line in lines:
                if one_line:
                    if '-----360 video parameters----' in one_line:
                        break
                    if 'Non-environment-variable-controlled' in one_line:
                        break
                    if one_line.count(':') == 1:
                        clean_line = one_line.strip(' \n\t\r')
                        clean_line = re.sub('\s+', '', clean_line)
                        if not any(re.search(param, clean_line) for param in param_not_considered):
                            cleanlist.append(clean_line)
                    elif one_line.count(':') > 1:
                        if re.search('\w+ \s+ \w+ \s+ \w+ \s+ :\s+ \( \w+ : \d+ , \s+ \w+ : \d+ \)', one_line, re.X):
                            clean_line = re.findall('\w+ \s+ \w+ \s+ \w+ \s+ :\s+ \( \w+ : \d+ , \s+ \w+ : \d+ \)',
                                                    one_line, re.X)
                        else:
                            clean_line = re.findall('\w+ : \d+ | \w+ : \s+ \w+ = \d+', one_line, re.X)
                        for clean_item in clean_line:
                            if not any(re.search(param, clean_item) for param in param_not_considered):
                                cleanlist.append(clean_item)

        parsed_config = dict(item.split(':', maxsplit=1) for item in cleanlist)

        # parse 360 rotation parameter
        m = re.search('Rotation in 1/100 degrees:\s+\(yaw:(\d+)\s+pitch:(\d+)\s+roll:(\d+)\)', log_text)
        if m:
            yaw = m.group(1)
            pitch = m.group(2)
            roll = m.group(3)
            parsed_config['SVideoRotation'] = 'Y%sP%sR%s' % (yaw, pitch, roll)

        self.qp = parsed_config['QP']
        return parsed_config

    def _parse_summary_data(self):

        with open(self.path, 'r') as log_file:
            log_text = log_file.read()
            total_time = re.findall(r""" ^\s*Total\s+Time.\s+(\d+.\d+)
                            """, log_text, re.M + re.X)

        # get 360 Lib version
        m = re.match(r'-----360Lib\ software\ version\ (\[3.0\])-----', log_text)
        if m:
            version = m.group(1)
        else:
            version = '0'

        # dictionary for the parsed data
        data = {}

        # get the summaries as pair of summary type and summary text, splitting at summary type and capturing it
        summaries_texts_and_types = re.split('((?:\w )?\w+) ?--------------------------------------------------------',
                                             log_text)
        del summaries_texts_and_types[0]  # remove the log text up to the first summary item
        if len(summaries_texts_and_types) % 2:
            # each summary type should match a text, thus the list must have even length
            raise Exception('Could not parse 360 enc log file.')
        for summary_type, summary_text in zip(summaries_texts_and_types[0::2], summaries_texts_and_types[1::2]):
            summary_text = summary_text.strip().splitlines()  # first line is header, second line are the values

            # parsing header
            first_header_item, remaining_items = re.split('\|', summary_text[0])  # since first item has a space
            remaining_items = re.split('\s+', remaining_items.strip())
            header = [first_header_item] + remaining_items

            # parsing values
            values = re.split('\s+', summary_text[1].strip())
            del values[1]  # remove the letter below the | in the header (a, b, p or i)

            if header[1] != 'Bitrate':
                raise Exception('Could not parse bitrate.')
            rate = values[1]

            data[summary_type] = {}
            for name, value in zip(header, values):
                name = name.strip()
                summary_item = {name: [(float(rate), float(value))]}

                data[summary_type].update(summary_item)

            if summary_type == 'SUMMARY':
                data['SUMMARY']['Total Time'] = [(float(rate), float(total_time[0]))]
                data['SUMMARY']['360Lib Version'] = [(float(rate), float(version))]

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
                \[ \S+ \s \S+ \s \S+ \s+ \S+ \s \S+ \s \S+ \s+ \S+ \s \S+ \s \S+ ] \s  #y-, u-, v-CFSPSNR_NN
                \[ \S+ \s \S+ \s \S+ \s+ \S+ \s \S+ \s \S+ \s+ \S+ \s \S+ \s \S+ ] \s  #y-, u-, v-CFSPSNR_I
                \[ \S+ \s \S+ \s \S+ \s+ \S+ \s \S+ \s \S+ \s+ \S+ \s \S+ \s \S+ ] \s  #y-, u-, v-CFCPPPSNR
                \[ \D+ \s+ (\d+) \s+ #ET
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
                 24: 'Y-PSNR_VP1', 25: 'U-PSNR_VP1', 26: 'V-PSNR_VP1', 27: 'ET'
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
        matches_class = cls._enc_log_file_matches_re_pattern(path, r'^SHM \s software')
        is_finished = cls._enc_log_file_matches_re_pattern(path, 'Total\ Time')
        return matches_class and is_finished

    def _parse_summary_data(self):
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            summaries = re.findall(r"""
                        ^\s+ L (\d+) \s+ (\d+) \s+ \D \s+ # the next is bitrate
                        (\S+) \s+ (\S+) \s+ (\S+) \s+ (\S+) \s+ (\S+)
                        """, log_text, re.M + re.X)
            total_time = re.findall(r""" ^\s*Total\s+Time.\s+(\d+.\d+)
                                        """, log_text, re.M + re.X)
        data = {}
        layer_quantity = int(len(summaries) / 4)
        header_names = ['SUMMARY', 'I', 'P', 'B']
        names = {1: 'Frames', 2: 'Bitrate', 3: 'Y-PSNR', 4: 'U-PSNR',
                 5: 'V-PSNR', 6: 'YUV-PSNR', }

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

            # add the addition of layers 1 and two in rate. PSNR values are taken from Layer one
            # TODO make this nice one day
            layerstring = 'layer 1 + 2'
            # data2[layerstring] = {}
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

        data['SUMMARY']['layer 0']['Total Time'] = [(float(summaries[0][2]), float(total_time[0]))]
        data['SUMMARY']['layer 1']['Total Time'] = [(float(summaries[1][2]), float(total_time[0]))]
        data['SUMMARY']['layer 1 + 2']['Total Time'] = [
            (float(data['SUMMARY']['layer 1 + 2']['Bitrate'][0][0]), float(total_time[0]))]
        return data

    def _parse_temporal_data(self):
        # this function extracts temporal values
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            temp_data = re.findall(r"""
                                ^POC \s+ (\d+) .+? : \s+ (\d+) .+ (\D-\D+) \s \D+,  #Slice
                                .+ \) \s+ (\d+) \s+ (.+) \s+ \[ (\D+) \s+ (\d+.\d+) \s+ #Y PSNR
                                \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ # U PSNR
                                \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ \D+ . # v PSNR
                                \s+ \[ (\D+) \s+ (\d+) \s+# Encoding time
                                """, log_text, re.M + re.X)

        # Association between index of data in temp_data and corresponding
        # output key. Output shape definition is in one place.
        names = {0: 'Frames', 3: 'Bits', 6: 'Y-PSNR', 8: 'U-PSNR',
                 10: 'V-PSNR', 12: 'ET'}

        layer_quantity = int(max(temp_data[i][1] for i in range(0, len(temp_data)))) + 1
        layer_quantity = int(layer_quantity)
        data = {}
        for layer in range(0, layer_quantity):  # iterate through layers
            data2 = {name: [] for (index, name) in names.items()}
            for j in range(0, int(len(temp_data) / layer_quantity)):  # iterate through frames (POCS)
                for (index, name) in names.items():
                    data2[name].append(
                        (j, temp_data[layer_quantity * j + layer][index])
                    )
            layerstring = 'layer ' + str(layer)
            data[layerstring] = data2
        return data

    def _parse_config(self):
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()                 # reads the whole text file
            lines = log_text.split('\n')
            clean_list = []
            for one_line in lines:
                if '=== Common configuration settings === ' in one_line:
                    break
                if re.match('QP\s+',one_line):
                    clean_line = one_line.strip(' \n\t\r')
                    clean_line = re.sub('\s+', '', clean_line)
                    clean_list.append(clean_line)
            clean_list = [item.split(':', maxsplit=1) for item in clean_list]
            parsed_config = {}
            for key, val in clean_list:
                # Later the differences between the configurations are calculated.
                # The calculation can not handle lists. Therefore the list elements are joined.
                # The first element describes the QP value connected to the first layer
                # and the second QP value connected to the second layer
                # TODO: connect QP values better to layers
                if key in parsed_config:
                    parsed_config.setdefault(key, []).append(val)
                    parsed_config[key] = '+'.join(parsed_config[key])
                else:
                    parsed_config.setdefault(key, []).append(val)
            self.qp = parsed_config['QP']
        return parsed_config


class EncLogVTM360Lib(AbstractEncLog):
    # Order value, used to determine order in which parser are tried.
    parse_order = 22

    @classmethod
    def can_parse_file(cls, path):
        matches_vtm_bms = cls._enc_log_file_matches_re_pattern(path, r'^VVCSoftware')    
        matches_360 = cls._enc_log_file_matches_re_pattern(path, r'Y-E2ESPSNR')
        is_finished = cls._enc_log_file_matches_re_pattern(path, 'Total\ Time')
        return matches_vtm_bms and is_finished and matches_360

    def _parse_path(self, path):
        """ parses the identifiers for an encoder log out of the
        path of the logfile and the sequence name and qp given in
         the logfile"""
        # set config to path of sim data item
        config = dirname(normpath(path))
        # get sequence name and qp from file name
        (_, filename) = split(path)

        name_and_rest  = re.split(r'_\d+x\d+_', filename)
        sequence = name_and_rest[0]
        
        m = re.match(r'QP(\d\d)_', name_and_rest[1])
        self.qp = m.group(1)

        return sequence, config

    def _parse_config(self):
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            lines = log_text.split('\n')
            cleanlist = []
            # some of the configs should not be interpreted as parameters
            # those are removed from the cleanlist
            param_not_considered = ['RealFormat', 'Warning', 'InternalFormat', 'Byteswrittentofile', 'Frameindex',
                                    'TotalTime', 'VVCSoftware']
            for one_line in lines:
                if one_line:
                    if '-----360 video parameters----' in one_line:
                        break
                    if 'Non-environment-variable-controlled' in one_line:
                        break
                    if one_line.count(':') == 1:
                        clean_line = one_line.strip(' \n\t\r')
                        clean_line = re.sub('\s+', '', clean_line)
                        if not any(re.search(param, clean_line) for param in param_not_considered):
                            cleanlist.append(clean_line)
                    elif one_line.count(':') > 1:
                        if re.search('\w+ \s+ \w+ \s+ \w+ \s+ :\s+ \( \w+ : \d+ , \s+ \w+ : \d+ \)', one_line, re.X):
                            clean_line = re.findall('\w+ \s+ \w+ \s+ \w+ \s+ :\s+ \( \w+ : \d+ , \s+ \w+ : \d+ \)',
                                                    one_line, re.X)
                        else:
                            clean_line = re.findall('\w+ : \d+ | \w+ : \s+ \w+ = \d+', one_line, re.X)
                        for clean_item in clean_line:
                            if not any(re.search(param, clean_item) for param in param_not_considered):
                                cleanlist.append(clean_item)

        parsed_config = dict(item.split(':', maxsplit=1) for item in cleanlist)

        # parse 360 rotation parameter
        m = re.search('Rotation in 1/100 degrees:\s+\(yaw:(\d+)\s+pitch:(\d+)\s+roll:(\d+)\)', log_text)
        if m:
            yaw = m.group(1)
            pitch = m.group(2)
            roll = m.group(3)
            parsed_config['SVideoRotation'] = 'Y%sP%sR%s' % (yaw, pitch, roll)

        # add qp from file name to config
        parsed_config['QP'] = self.qp

        return parsed_config

    def _parse_summary_data(self):

        with open(self.path, 'r') as log_file:
            log_text = log_file.read()
            total_time = re.findall(r""" ^\s*Total\s+Time.\s+(\d+.\d+)
                            """, log_text, re.M + re.X)

            # get 360 Lib version                        
            version360Lib = re.findall(r'-----360Lib\ software\ version\ \[(\d.\d)\]-----', log_text)
            if not version360Lib:
                version360Lib = 0

            # dictionary for the parsed data
            data = {}

            # get the summaries as pair of summary type and summary text, splitting at summary type and capturing it
            summaries_texts_and_types = re.split('Total Frames',
                                                log_text)
            del summaries_texts_and_types[0]  # remove the log text up to the first summary item

            summaries_texts_and_types = summaries_texts_and_types[0]
            summaries_texts_and_types = 'Total Frames' + summaries_texts_and_types
            summary_text = summaries_texts_and_types.strip().splitlines()





            # for summary_type, summary_text in zip(summaries_texts_and_types[0::2], summaries_texts_and_types[1::2]):
            # summary_text = summary_text.strip().splitlines()  # first line is header, second line are the values

            # parsing header
            first_header_item, remaining_items = re.split('\|', summary_text[0])  # since first item has a space
            remaining_items = re.split('\s+', remaining_items.strip())
            header = [first_header_item] + remaining_items

            # parsing values
            values = re.split('\s+', summary_text[1].strip())
            del values[1]  # remove the letter below the | in the header (a, b, p or i)

            if header[1] != 'Bitrate':
                raise Exception('Could not parse bitrate.')
            rate = values[1]
            
            summary_type = 'SUMMARY'
            data[summary_type] = {}
            for name, value in zip(header, values):
                name = name.strip()
                summary_item = {name: [(float(rate), float(value))]}

                data[summary_type].update(summary_item)

            if summary_type == 'SUMMARY':
                data['SUMMARY']['Total Time'] = [(float(rate), float(total_time[0]))]
                data['SUMMARY']['360Lib Version'] = [(float(rate), float(version360Lib[0]))]

            return data


class EncLogVTM(AbstractEncLog):
    # Order value, used to determine order in which parser are tried.
    parse_order = 23

    @classmethod
    def can_parse_file(cls, path):
        matches_vtm_bms = cls._enc_log_file_matches_re_pattern(
            path, r'^VVCSoftware')
        is_finished = cls._enc_log_file_matches_re_pattern(
            path, r'Total\ Time')
        return matches_vtm_bms and is_finished

    def _parse_path(self, path):
        """ parses the identifiers for an encoder log out of the
        path of the logfile and the sequence name and qp given in
         the logfile"""
        # set config to path of sim data item
        config = dirname(normpath(path))
        # get sequence name and qp from file name
        (_, filename) = split(path)

        name_and_rest = re.split(r'_\d+x\d+_', filename)
        sequence = name_and_rest[0]

        m = re.match(r'QP(\d\d)_', name_and_rest[1])
        self.qp = m.group(1)

        return sequence, config

    def _parse_config(self):

        parsed_config = {}

        # add qp from file name to config
        parsed_config['QP'] = self.qp

        return parsed_config

    def _parse_summary_data(self):

        with open(self.path, 'r') as log_file:
            log_text = log_file.read()

            # dictionary for the parsed data
            data = {}

            # get the summaries as pair of summary type and summary text,
            # splitting at summary type and capturing it
            summaries_texts_and_types = re.split('Total Frames', log_text)
            del summaries_texts_and_types[
                0]  # remove the log text up to the first summary item

            summaries_texts_and_types = summaries_texts_and_types[0]
            summaries_texts_and_types = 'Total Frames' + summaries_texts_and_types
            summary_text = summaries_texts_and_types.strip().splitlines()

            # parsing header
            first_header_item, remaining_items = re.split(
                '\|', summary_text[0])  # since first item has a space
            remaining_items = re.split('\s+', remaining_items.strip())
            header = [first_header_item] + remaining_items

            # parsing values
            values = re.split('\s+', summary_text[1].strip())
            del values[
                1]  # remove the letter below the | in the header (a, b, p or i)

            if header[1] != 'Bitrate':
                raise Exception('Could not parse bitrate.')
            rate = values[1]

            summary_type = 'SUMMARY'
            data[summary_type] = {}
            for name, value in zip(header, values):
                name = name.strip()
                summary_item = {name: [(float(rate), float(value))]}

                data[summary_type].update(summary_item)

            return data

    def _parse_temporal_data(self):
        return {}


class EncLogVTMRPR(AbstractEncLog):
    # Order value, used to determine order in which parser are tried.
    parse_order = 25

    @classmethod
    def can_parse_file(cls, path):
        matches_vtm_bms = cls._enc_log_file_matches_re_pattern(
            path, r'^VVCSoftware')
        matches_rpr = cls._enc_log_file_matches_re_pattern(path, r'PSNR1')
        is_finished = cls._enc_log_file_matches_re_pattern(
            path, r'Total\ Time')
        return matches_vtm_bms and is_finished and matches_rpr

    def _parse_path(self, path):
        """ parses the identifiers for an encoder log out of the
        path of the logfile and the sequence name and qp given in
         the logfile"""
        # set config to path of sim data item
        config = dirname(normpath(path))
        # get sequence name and qp from file name
        (_, filename) = split(path)

        name_and_rest = re.split(r'_\d+x\d+_', filename)
        sequence = name_and_rest[0]

        m = re.match(r'QP(\d\d)_', name_and_rest[1])
        self.qp = m.group(1)

        return sequence, config

    def _parse_config(self):

        parsed_config = {}

        # add qp from file name to config
        parsed_config['QP'] = self.qp

        return parsed_config

    def _parse_summary_data(self):

        with open(self.path, 'r') as log_file:
            log_text = log_file.read()

            # dictionary for the parsed data
            data = {}

            # get the summaries as pair of summary type and summary text,
            # splitting at summary type and capturing it
            summaries_texts_and_types = re.split('Total Frames', log_text)
            del summaries_texts_and_types[
                0]  # remove the log text up to the first summary item

            summaries_texts_and_types = summaries_texts_and_types[0]
            summaries_texts_and_types = 'Total Frames' + summaries_texts_and_types
            summary_text = summaries_texts_and_types.strip().splitlines()

            # parsing header
            first_header_item, remaining_items = re.split(
                '\|', summary_text[0])  # since first item has a space
            remaining_items = re.split('\s+', remaining_items.strip())
            header = [first_header_item] + remaining_items

            # parsing values
            values = re.split('\s+', summary_text[1].strip())
            del values[
                1]  # remove the letter below the | in the header (a, b, p or i)

            if header[1] != 'Bitrate':
                raise Exception('Could not parse bitrate.')
            rate = values[1]

            summary_type = 'SUMMARY'
            data[summary_type] = {}
            for name, value in zip(header, values):
                name = name.strip()
                summary_item = {name: [(float(rate), float(value))]}

                data[summary_type].update(summary_item)

            # parse values for PSNR1 and PSNR2
            header = re.split('\s+', summary_text[3].strip())
            values = re.split('\s+', summary_text[4].strip())

            summary_type = header.pop(0)
            data[summary_type] = {}
            for name, value in zip(header, values):
                name = name.strip()
                summary_item = {name: [(float(rate), float(value))]}

                data[summary_type].update(summary_item)

            # parse values for PSNR1
            header = re.split('\s+', summary_text[5].strip())
            values = re.split('\s+', summary_text[6].strip())

            summary_type = header.pop(0)
            data[summary_type] = {}
            for name, value in zip(header, values):
                name = name.strip()
                summary_item = {name: [(float(rate), float(value))]}

                data[summary_type].update(summary_item)

            # parse values and calculate PSNR-3,
            # this is the PSNR off all frames including downsampled frames in their
            # reference picture list
            bits_ypsnr = re.findall(
                r"(\d+) bits \[Y (\d+\.\d+) dB.*\(0.50x, 0.50x\).*", log_text)
            bits = list(map(list, zip(*bits_ypsnr)))[0]
            bits = list(map(float, bits))
            bits = sum(bits) / bits.__len__()  # calculate bits per frame
            y_psnr = list(map(list, zip(*bits_ypsnr)))[1]
            y_psnr = list(map(float, y_psnr))
            y_psnr = sum(y_psnr) / y_psnr.__len__()  # calculate average y-psnr
            data['PSNR3'] = {'Y-PSNR': [(bits, y_psnr)]}

            # parse values and calculate PSNR-4,
            # this is the PSNR at upsampling points only
            bits_ypsnr = re.findall(
                r"(\d+) bits \[Y (\d+\.\d+) dB.*\[L0 \d+(?:\(0.50x, 0.50x\)|\(AddRef\)).*", log_text)
            bits = list(map(list, zip(*bits_ypsnr)))[0]
            bits = list(map(float, bits))
            print(bits.__len__())
            bits = sum(bits) / bits.__len__()  # calculate bits per frame
            y_psnr = list(map(list, zip(*bits_ypsnr)))[1]
            y_psnr = list(map(float, y_psnr))
            y_psnr = sum(y_psnr) / y_psnr.__len__()  # calculate average y-psnr
            data['PSNR4'] = {'Y-PSNR': [(bits, y_psnr)]}

            return data

    def _parse_temporal_data(self):
        return {}
