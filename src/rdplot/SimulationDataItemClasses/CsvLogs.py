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
###############################################################################

from rdplot.SimulationDataItem import AbstractSimulationDataItem


class CSVLog(AbstractSimulationDataItem):
    def __init__(self, config, header, line):
        # we do not have a unique path for each simulation data item
        # in the case of a csv file. Abuse the line as unique identifier
        # there should'nt be any equal lines
        super().__init__(line)

        header = header.replace("\n", "")
        header = header.lower().split(';')
        sequence_idx = header.index("sequence")
        qp_idx = header.index("qp")

        # split also the line
        line = line.split(';')

        # I want to allow for all header fields looking like the bitrate
        # Therefore, it is a little bit more complicated here
        tmp = list(map(lambda x: 'rate' in x, header))
        rate_idx = tmp.index(1)
        rate = float(line[rate_idx])

        self.sequence = line[sequence_idx]
        self.qp = line[qp_idx]
        self.config = config

        data = {}
        for i in range(0, len(header)):
            if i in [sequence_idx, qp_idx, rate_idx]:
                continue
            data[header[i]] = [(rate, float(line[i]))]
        self.summary_data = data

    @property
    def tree_identifier_list(self):
        return [self.__class__.__name__, self.sequence, self.config, self.qp]

    @property
    def data(self):
        # TODO we may want to have more data than summary and temporal
        # e.g. runtime over qp
        return [
            (
                [self.sequence, self.config],
                {'Summary': self.summary_data}
            )
        ]

    def _get_label(self, keys):
        """
        :param keys: Variable/Path for which to get the labels
        :return: tuple of labels: (x-axis label, y-axis label)
        """
        label = ('kbps', 'dB')

        return label

    def _parse_config(self):
        # we don't need to parse a config here,
        # it comes from the name of the csv file
        pass

    def can_parse_file(self):
        # we assume that we can parse it for the moment
        pass

    # Non-abstract Helper Functions
    @classmethod
    def _enc_log_file_matches_re_pattern(cls, path, pattern):
        """"""
        if path.endswith(".csv"):
            return cls._is_file_text_matching_re_pattern(path, pattern)
        return False

