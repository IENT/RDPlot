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
from abc import abstractmethod
from xml.parsers.expat import ExpatError
from os.path import normpath, basename, sep, dirname

from rdplot.SimulationDataItem import (AbstractSimulationDataItem, SimulationDataItemError)


class AbstractDatLog(AbstractSimulationDataItem):
    def __init__(self, path):
        super().__init__(path)

        with open(self.path, 'r') as dat_log:
            xml = dat_log.read()
            sim_data = xmltodict.parse(xml)
            sim_data = sim_data['Logfile']
            # store the parsed xml dict
            self.sim_data = sim_data

        # Parse file path and set additional identifiers
        # self.logType = self._get_Type(path)
        self.sequence, self.config, self.qp = self._parse_path(self.path)

        # Dictionaries holding the parsed values
        self.summary_data = self._parse_summary_data()
        self.temporal_data = self._parse_temporal_data()

        self.log_config = self._parse_config()

    def _parse_path(self, path):
        """ parses the identifiers for an encoder log out of the
        path of the logfile and the sequence name and qp given in
         the logfile"""
        # set config to path of sim data item
        config = dirname(normpath(path))
        sim_data = self.sim_data

        sequence = sim_data['SeqName']['Value']
        qp = sim_data['QP']['Value']

        return sequence, config, qp

    # Properties

    @property
    def tree_identifier_list(self):
        return ["XML-Datlog", self.sequence, self.config, self.qp]

    @abstractmethod
    def _parse_config(self):
        """Method which parses log file to get config (QP, other parameters).
        Abstract, needs to be implemented by log parsers
        :return:
        """
        pass

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


class XMLDatLog(AbstractDatLog):
    @classmethod
    def can_parse_file(cls, path):
            try:
                with open(path, 'r') as dat_log:
                    xml = dat_log.read()
                xmltodict.parse(xml)
                # if we can parse the xml file, assume that RDPlot can display the data
                return True
            except (ExpatError, UnicodeDecodeError, KeyError, IsADirectoryError,FileNotFoundError, PermissionError) as err:
                return False

    def _parse_summary_data(self):
        try:
            # create local copy of sim data. we don't want to delete the rate field outside of this function
            sim_data = dict(self.sim_data)
            rate = float(sim_data['Rate']['Value'])
            del sim_data['Rate']

            data = {}
            for key, value in sim_data.items():
                if 'temporal_data' == key:
                    continue
                try:
                    data[key] = [(rate, float(sim_data[key]['Value']))]
                except ValueError:
                    print("Could not convert %s: %s to float" % (key,sim_data[key]['Value'] ))
                    continue

            return data
        except IndexError:
            raise

    def _parse_temporal_data(self):
        try:
            # create local copy of sim data. we don't want to delete the rate field outside of this function
            sim_data = dict(self.sim_data)
            data = {}

            if 'temporal_data' in sim_data:
                temporal_data = sim_data['temporal_data']
                for frame_string, frame_items in temporal_data.items():
                    frame_nr = int(frame_string.split('Frame')[1])
                    for key, item_desc in frame_items.items():
                        try:
                            if not key in data:
                                # start new list
                                data[key] = [(frame_nr, float(item_desc['Value']))]
                            else:
                                # append to list
                                data[key] += [(frame_nr, float(item_desc['Value']))]
                        except ValueError:
                            print("Could not convert %s: %s to float" % (key,sim_data[key]['Value'] ))
                            continue
            else:
                return {}
            return data
        except IndexError:
            raise

    def _parse_config(self):
        """Method which parses log file to get config (QP, other parameters).
        Abstract, needs to be implemented by log parsers
        :return:
        """
        return {}  # in case no configuration information has been parsed return an empty dict

    def _get_label(self, keys):
        """
        :param keys: Variable/Path for which to get the labels
        :return: tuple of labels: (x-axis label, y-axis label)
        """
        sim_data = self.sim_data

        if keys[0] == 'Summary':
            unit_rate = sim_data['Rate']['Unit']
            label_x = unit_rate
        elif keys[0] == 'Temporal':
            label_x = 'Frame'
        else:
            label_x = 'dummy'

        if 'Unit' in sim_data[keys[-1]]:
            label_y = sim_data[keys[-1]]['Unit']
        else:
            label_y = 'dummy'

        return (label_x, label_y)
