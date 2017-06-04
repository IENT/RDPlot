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
import xmltodict
from xml.parsers.expat import ExpatError
from os.path import normpath, basename, sep, dirname

from SimulationDataItem import (AbstractSimulationDataItem,
                                SimulationDataItemError)


class AbstractDatLog(AbstractSimulationDataItem):
    def __init__(self, path):
        super().__init__(path)

        # Parse file path and set additional identifiers
        # self.logType = self._get_Type(path)
        self.sequence, self.config, self.qp = self._parse_path(self.path)

        # Dictionaries holding the parsed values
        self.summary_data = self._parse_summary_data()
        self.temporal_data = {}  # Dat logs have no temporal data

    def _parse_path(self, path):
        filename = basename(path)

        separator = '-'
        try:
            filename_split = filename.split('_QP')[0].split(separator)
            sequence = filename_split[-1]
            config = separator.join(filename_split[0: -2])
        except IndexError:
            raise SimulationDataItemError((
                "Filename {} can not be split into config until '{}' and"
                " sequence between last '{}' and '_QP'"
            ).format(filename, separator, separator))

        # prepend simulation directory to config
        config = dirname(normpath(path)) + config
        qp = None
        with open(self.path, 'r') as dat_log:
            try:
                xml = dat_log.read()
                sim_data = xmltodict.parse(xml)
                # TODO support for layer specific qp
                qp = sim_data['Logfile']['QP']['Value']
            except (IndexError, ExpatError):
                raise SimulationDataItemError

        return sequence, config, qp

    # Properties

    @property
    def tree_identifier_list(self):
        return [self.__class__.__name__, self.sequence, self.config, self.qp]

    @property
    def data(self):
        # TODO we may want to have more data than summary and temporal
        # e.g. runtime over qp
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


class DatLogBasedOnClassName(AbstractDatLog):
    @classmethod
    def can_parse_file(cls, path):
            try:
                with open(path, 'r') as dat_log:
                    xml = dat_log.read()
                sim_data = xmltodict.parse(xml)
                # discard 'DatLog' from class name, then compare to class specified in log file
                is_sim_of_this_class = ( cls.__name__[6:]  in sim_data['Logfile']['Codec']['Value'])
                return is_sim_of_this_class
            except (ExpatError, UnicodeDecodeError, KeyError, IsADirectoryError):
                return False

    def _parse_summary_data(self):
        with open(self.path, 'r') as dat_log:
            try:
                xml = dat_log.read()
                sim_data = xmltodict.parse(xml)
                sim_data = sim_data['Logfile']
                rate = float(sim_data['Rate']['Value'])
                del sim_data['Rate']

                data = {}
                for key, value in sim_data.items():
                    try:
                        data[key] = [(rate, float(sim_data[key]['Value']))]
                    except ValueError:
                        print("Could not convert %s: %s to float" % (key,sim_data[key]['Value'] ))
                        continue

                return data
            except IndexError:
                raise


class DatLogHEVC(DatLogBasedOnClassName):
    pass


class DatLogJEM501_360(DatLogBasedOnClassName):
    pass