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
from os.path import normpath, basename, dirname
from abc import abstractclassmethod

from rdplot.SimulationDataItem import AbstractSimulationDataItem, SimulationDataItemError


class AbstractDecAnalyserLog(AbstractSimulationDataItem):
    def __init__(self, path):
        super().__init__(path)

        # Parse file path and set additional identifiers
        # self.logType = self._get_Type(path)
        self.sequence, self.config, self.qp = self._parse_path(self.path)

        # Dictionaries holding the parsed values
        self.analyser_data = self._parse_analyser_data()

        self.log_config = self._parse_config()

    def _parse_path(self, path):
        """ parses the identifiers for an encoder log out of the
        path of the logfile and the sequence name and qp given in
         the logfile"""
        # set config to path of sim data item
        config = dirname(normpath(path))

        # decoder logs do not contain description of the related sequence, have to parse all from file name
        try:
            sequence = re.search("(\w+)_\d+x\d+", basename(path)).group(1)
            qp = re.search("_QP(\d+)_", basename(path)).group(1)
        except:  # could not get name and qp from file name
            raise SimulationDataItemError

        self.qp = float(qp)

        return sequence, config, qp

    def _get_label(self, keys):
        """
        :param keys: Variable/Path for which to get the labels
        :return: tuple of labels: (x-axis label, y-axis label)
        """

        # everything is plotted over QP:
        label = ('QP', keys[-1])

        return label

    # Properties

    @property
    def tree_identifier_list(self):
        return [self.__class__.__name__, self.sequence, self.config, self.qp]

    @abstractclassmethod
    def _parse_config(self):
        """Method which parses log file to get config (QP, other parameters).
        Abstract, needs to be implemented by log parsers
        :return:
        """
        pass

    @property
    def data(self):
        # e.g. count of ref frm idx bytes over qp
        return [
            (
                [self.sequence, self.config],
                {'Analyser': self.analyser_data}
            ),
        ]

    # Non-abstract Helper Functions
    @classmethod
    def _enc_log_file_matches_re_pattern(cls, path, pattern):
        """"""
        if path.endswith("dec.log"):
            return cls._is_file_text_matching_re_pattern(path, pattern)
        return False


class DecAnalyserLogHM(AbstractDecAnalyserLog):
    # at the moment not the complete decoder analyser log is parsed. the bySize and bySize/byType values are left out

    # Order value, used to determine order in which parser are tried.
    parse_order = 10

    @classmethod
    def can_parse_file(cls, path):
        matches_class = cls._enc_log_file_matches_re_pattern(path, r'^HM \s software')
        is_finished = cls._enc_log_file_matches_re_pattern(path, '\[TOTAL')
        return matches_class and is_finished

    def _parse_analyser_data(self):
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file

            # we are only interested in the statistics. splitting the file at the line with 'Decoder statistics'
            dec_statistics = re.split('Decoder statistics', log_text)[1]
            # each statistic has its own line:
            dec_statistics = re.split('\n', dec_statistics)

            data = dict()
            data['Total'] = {}

            variables_list = ['CABAC Count', 'CABAC Sum', 'CABAC bits', 'EP Count', 'EP Sum', 'EP bits', 'Total bits',
                              'Total bytes']

            # process each line
            for statistic in dec_statistics:
                # try to match non total items
                m = re.match(
                    '\s*(\S+)\s*:' +         # name
                    '\s*(\S+)' +             # width
                    '\s*(\S+)' +             # type
                    '\s*(\S+)' +             # CABAC Count
                    '\s*(\S+)' +             # CABAC Sum
                    '\s*(\S+)' +             # CABAC bits
                    '\s*(\S+)' +             # EP Count
                    '\s*(\S+)' +             # EP Sum
                    '\s*(\S+)' +             # EP bits
                    '\s*(\S+)' +             # Total bits
                    '\s*\(\s*(\S+)\)',       # Total bytes
                    statistic)
                if m:
                    statistic_name = m.group(1)
                    statistic_width = m.group(2)
                    statistic_type = m.group(3)

                    # create type, width, statistic name if not existing
                    if statistic_type not in data:
                        data[statistic_type] = {}
                    if statistic_width not in data[statistic_type]:
                        data[statistic_type][statistic_width] = {}
                    if statistic_name not in data[statistic_type][statistic_width]:
                        data[statistic_type][statistic_width][statistic_name] = {}

                    for idx, var_name in enumerate(variables_list):
                        # Reference all data to bit rate
                        data[statistic_type][statistic_width][statistic_name][var_name] = []
                        # add an entry for each variable in variables_list
                        data[statistic_type][statistic_width][statistic_name][var_name].append(
                            (self.qp, float(m.group(idx + 4))))
                        pass

                    continue

                # try to match total items
                m = re.match(
                    '\[(\S+)\s*~' +          # name
                    '\s*(\S+)' +             # width
                    '\s*(\S+)' +             # type
                    '\s*(\S+)' +             # CABAC Count
                    '\s*(\S+)' +             # CABAC Sum
                    '\s*(\S+)' +             # CABAC bits
                    '\s*(\S+)' +             # EP Count
                    '\s*(\S+)' +             # EP Sum
                    '\s*(\S+)' +             # EP bits
                    '\s*(\S+)' +             # Total bits
                    '\s*\(\s*(\S+)\)\]',     # Total bytes
                    statistic)
                if m:
                    statistic_name = m.group(1)

                    # create  statistic name if not existing
                    if statistic_name not in data['Total']:
                        data['Total'][statistic_name] = {}

                    for idx, var_name in enumerate(variables_list):
                        # Reference all data to qp
                        data['Total'][statistic_name][var_name] = []
                        # add an entry for each variable in variables_list
                        data['Total'][statistic_name][var_name].append((self.qp, float(m.group(idx + 4))))
                        pass

                    continue

        return data

    def _parse_config(self):
        """Method which parses log file to get config (QP, other parameters).
        Abstract, needs to be implemented by log parsers
        :return:
        """
        return {}  # in case no configuration information has been parsed return an empty dict
