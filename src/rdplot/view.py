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
import json
from collections import deque
from os.path import isdir, abspath, sep, dirname, basename, isfile, join
from pathlib import Path, PureWindowsPath
import jsonpickle
from PyQt5 import QtWidgets
from PyQt5.Qt import QApplication
from PyQt5.QtCore import *
from PyQt5.QtCore import QObject, QItemSelectionModel, QItemSelection, QModelIndex, pyqtSignal, QThread
from PyQt5.QtGui import *
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QMessageBox, QMenu, QListView
from pathlib import Path

from rdplot.SimulationDataItem import SimulationDataItemFactory, SimulationDataItemError
from rdplot.model import AmbiguousSimDataItems

# Path to the folder containing simulation data sub classes. The classes
# are loaded by the simulation data item factory and used for parsing files
here = abspath(dirname(__file__))
SIMULATION_DATA_ITEM_CLASSES_PATH = here + sep + "SimulationDataItemClasses"


class ParserWorkThread(QThread):
    newParsedData = pyqtSignal([list])
    allParsed = pyqtSignal()
    parsingError = pyqtSignal()

    def __init__(self, path_list=None):
        QThread.__init__(self)

        self._factory = SimulationDataItemFactory.from_path(
            SIMULATION_DATA_ITEM_CLASSES_PATH
        )

        if path_list is None:
            path_list = []
        self.path_list = path_list

        self._factory.parsingError.connect(self.relay_error)

    def __del__(self):
        self.wait()

    def add_path(self, path):
        self.path_list.append(path)

    def run(self):
        for path in self.path_list:
            try:
                sim_data_items = self._factory.create_item_list_from_path(path)
                print("Parsed '{}' ".format(path))
            except SimulationDataItemError:
                self.newParsedData.emit([])
                self.path_list.clear()
                return

            self.newParsedData.emit(sim_data_items)
        self.path_list.clear()
        self.allParsed.emit()

    def relay_error(self):
        self.parsingError.emit()

    def showMsgBox(self):
        return False


class ParserWorkNoThread(QObject):
    """
    This class is intended to be used to make debugging easier,
    when breakpoints don't work because of threading
    """

    newParsedData = pyqtSignal([list])
    allParsed = pyqtSignal()
    parsingError = pyqtSignal()

    def __init__(self, path_list=None):
        QObject.__init__(self)

        self._factory = SimulationDataItemFactory.from_path(
            SIMULATION_DATA_ITEM_CLASSES_PATH
        )

        if path_list is None:
            path_list = []
        self.path_list = path_list

        self._factory.parsingError.connect(self.relay_error)

    def __del__(self):
        self.wait()

    def add_path(self, path):
        self.path_list.append(path)

    def run(self):
        for path in self.path_list:
            try:
                sim_data_items = self._factory.create_item_list_from_path(path)
                print("Parsed '{}' ".format(path))
            except SimulationDataItemError:
                self.newParsedData.emit([])
                self.path_list.clear()
                return

            self.newParsedData.emit(sim_data_items)
        self.path_list.clear()
        self.allParsed.emit()

    def relay_error(self):
        self.parsingError.emit()

    def start(self):
        self.run()

    def showMsgBox(self):
        return False


class SimDataItemTreeView(QtWidgets.QTreeView):

    deleteKey = pyqtSignal()
    itemsOpened = pyqtSignal(list, bool)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.parserThread = ParserWorkThread()
        # helpful for debugging, when breakpoints don't work because of threading
        self.parserThread = ParserWorkNoThread()
        self.parserThread.newParsedData.connect(self._update_model)
        self.parserThread.allParsed.connect(self._hide_parse_message)
        self.msg = QMessageBox(self)  # use self as parent here
        self.msg.setIcon(QMessageBox.Information)
        self.msg.setText("Parsing Directory...")
        self.msg.setWindowTitle("Info")
        # TODO: add context menu capabilities
        # self.setContextMenuPolicy(Qt.CustomContextMenu)
        # self.customContextMenuRequested.connect(self.openMenu)
        self.errorMsg = QMessageBox(self)
        self.errorMsg.setText('The selected parser was unfortunately unable to correctly read in the files.')
        self.errorMsg.setWindowTitle('Error!')
        self.errorMsg.setIcon(QMessageBox.Warning)
        self.parserThread.parsingError.connect(self.errorMsg.show)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

    # drag'n'drop mechanism adapted
    # from question on stackoverflow at http://stackoverflow.com/q/22543644
    # from user http://stackoverflow.com/users/1107049/alphanumeric

    def dragEnterEvent(self, event):
        # Consider only url/path events
        if event.mimeData().hasUrls():
            event.accept()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if url.isLocalFile() and isfile(url.path()):
                try:
                    # check what kind of file we have.
                    # process .rd with load_rd_data, .xml and .log with the parsers
                    file_ending = file_path.suffix
                    if file_ending == '.rd':
                        self.load_rd_data(str(file_path))
                    elif file_ending == '.log' or file_ending == '.xml':
                        self.parserThread.add_path(str(file_path))
                        self.parserThread.start()
                except json.decoder.JSONDecodeError:
                    return
                except IndexError:  # there was no file ending, i.e. not '.' in the name
                    return
            else:
                if self.parserThread.showMsgBox():
                    self.msg.show()
                self.parserThread.add_path(file_path)
                self.parserThread.start()

    # end snippet

    # keypress fix adapted
    # from answer on stackoverflow at http://stackoverflow.com/a/27477021
    # from user http://stackoverflow.com/users/984421/ekhumoro

    def keyPressEvent(self, q_key_event):
        if q_key_event.count() == 1 and q_key_event.key() == Qt.Key_Delete:
            self.deleteKey.emit()
        super().keyPressEvent(q_key_event)

    # TODO: this is how context menus can be implemented    
    def open_menu(self, position):
        indexes = self.selectedIndexes()
        if len(indexes) > 0:
            level = 0
            index = indexes[0]
            while index.parent().isValid():
                index = index.parent()
                level += 1
        index_selected = self.indexAt(position)
        menu = QMenu()
        menu.addAction(self.tr("Level: " + str(level) + ", Index: " + str(index_selected)))
        menu.exec_(self.viewport().mapToGlobal(position))

    # end snippet

    def _get_open_file_names(self):
        # extract folder and filename
        try:
            result = QtWidgets.QFileDialog.getOpenFileNames(
                self,
                "Open Sequence Encoder Log",
                "/home/ient/Software/rd-plot-gui/exampleLogs",
                "All Logs (*.log *.xml *.rd);;Encoder Logs (*.log);;Dat Logs (*.xml);; RD Data (*.rd)")

            # magic: split returned list of files into lists of directories and file names
            directories, file_names = zip(*[file.rsplit('/', 1) for file in result[0]])
            return directories, file_names
        except (IndexError, ValueError):
            return

    def _get_folder(self):
        # extract folder and filename
        try:
            result = QtWidgets.QFileDialog.getExistingDirectory(
                self,
                "Open Directory",
                "/home/ient/Software/rd-plot-gui/exampleLogs")
            if not result:
                raise TypeError
            return result
        except IndexError:
            return

    # open one or more files
    # will detect what kind of file (.rd, .log, .xml) and act accordingly
    def add_file(self, path, reload=False):
        if not path:
            try:
                directories, file_names = self._get_open_file_names()
            except TypeError:
                return
            for directory, file_name in zip(directories, file_names):
                # check what kind of file we have.
                # process .rd with load_rd_data, .xml and .log with the parsers
                path = join(directory, file_name)
                file_ending = file_name.rsplit('.', maxsplit=1)[1]
                if file_ending == 'rd':
                    self.load_rd_data(path)
                elif file_ending == 'log' or file_ending == 'xml':
                    self.parserThread.add_path(path)
            self.parserThread.start()
            self.itemsOpened.emit(list(map(lambda x, y: x+'/'+y, directories, file_names)), reload)
        else:
            self.parserThread.add_path(path)
            self.parserThread.start()
            self.itemsOpened.emit([path], reload)

    # adds all log files and sequences from a directory to the treeview
    def add_folder(self, path=''):
        if not path:
            try:
                path = self._get_folder()
            except TypeError:
                return

        # TODO this uses the parse_directory method, thus, does not automatically
        # parse 'log'.subfolder. Should this be the case?
        # sim_data_items = list(SimulationDataItemFactory.parse_directory(path))
        # self.model().update(sim_data_items)
        if self.parserThread.showMsgBox():
            self.msg.show()
        self.parserThread.add_path(path)
        self.parserThread.start()
        self.itemsOpened.emit([path], False)

    def add_folder_list(self):
        try:
            result = QtWidgets.QFileDialog.getOpenFileNames(
                self,
                "Open Directory List",
                "/home/ient/Software/rd-plot-gui/exampleLogs",
                "Text Files (*.txt *.*)")

            with open(result[0][0]) as fp:
                for line in fp:
                    clean_path = line.rstrip()
                    if isdir(clean_path):
                        self.parserThread.add_path(clean_path)
                    self.itemsOpened.emit([clean_path], False)

            if self.parserThread.showMsgBox():
                self.msg.show()
            self.parserThread.start()

        except IndexError:
            return

            # TODO this uses the parse_directory method, thus, does not automatically
            # parse 'log'.subfolder. Should this be the case?
            # sim_data_items = list(SimulationDataItemFactory.parse_directory(path))
            # self.model().update(sim_data_items)
            # self.msg.show()
            # self.parserThread.addPath(path)
            # self.parserThread.start()

    def _hide_parse_message(self):
        self.msg.hide()

    def load_rd_data(self, filename):
        """Loads rd data from file"""
        f = open(filename, 'r')
        json_str = f.read()
        sim_data_items = jsonpickle.decode(json_str)
        self._update_model(sim_data_items)
        f.close()

    def _update_model(self, sim_data_items):
        if not sim_data_items:
            self._hide_parse_message()
            msg = QMessageBox(self)  # use self as parent here
            msg.setIcon(QMessageBox.Warning)
            msg.setText("I cannot find any simulation data item in your selected directory.\n"
                        "If you are really sure that there should be some valid item, "
                        "you should consider writing a new parser.")
            msg.setWindowTitle("Warning")
            msg.show()
        try:
            self.model().update(sim_data_items,False)
        except AmbiguousSimDataItems as inst:
            self._hide_parse_message()
            msg = QMessageBox(self)  # use self as parent here
            msg.setIcon(QMessageBox.Warning)
            msg.setText("I have found ambiguous simulation data items in your selected directory.\n"
                        "The reason for that is that you want to parse files from one directory "
                        "with different names but the same QP and sequence name.\n"
                        "From all the parsers I know at the moment I cannot decide what you want "
                        "to achieve.\n"
                        "Recommendation: Move the files you do not want plot to a different location.\n"
                        "Note: The sequence tree view on the left is most probably incomplete now.\n\n"
                        "%s" % inst)
            msg.setWindowTitle("Warning")
            msg.show()

        self.expandToDepth(0)


class PlottedFilesListView(QtWidgets.QListView):
    """Implements the view for plotted files"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def keyPressEvent(self, q_key_event):
        """Catches the CTRL+C KeyPressEvent"""
        if q_key_event.count() == 1 and q_key_event.matches(QKeySequence.Copy):
            str_list = []
            for q_index in self.selectedIndexes():
                str_list.append(q_index.data())

            QApplication.clipboard().setText("\n".join(str_list))


class QRecursiveSelectionModel(QItemSelectionModel):
    """Custom selection model for recursive models. If an item is selected, all
       sub items are automatically selected."""

    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setModel(model)

    def setModel(self, model):
        if self.model() is not None:
            self.model().items_changed.disconnect(self.select_inserted_rows)
        super().setModel(model)
        self.model().items_changed.connect(self.select_inserted_rows)

    def select_inserted_rows(self):
        self.select(self.selection(), QItemSelectionModel.Select)

    def select(self, selection, command):
        """Extend behavior of inherited method. Add all sub items to selection
           """
        # if the selection is a QModelIndex return und don do anything
        if isinstance(selection, QModelIndex):
            if not selection.isValid():
                self.clearSelection()
                return
            indexes_selected = [selection]
            # If the selection is an index, a range only containing this index
            # has to be created
            recursive_selection = QItemSelection()

            q_index_parent = self.model().parent(selection)
            q_index_first = selection
            q_index_last = self.model().index(selection.row(),
                                              selection.column(),
                                              q_index_parent)
            recursive_selection.select(q_index_first, q_index_last)

        # Handle selections and single indexes
        if isinstance(selection, QItemSelection):
            indexes_selected = selection.indexes()
            recursive_selection = selection

        # Find index ranges of all sub items of the indexes in `selection`
        index_ranges = self._get_sub_items_index_ranges(indexes_selected)
        # Add the index ranges to the `selection`
        for (q_index_1, q_index_2) in index_ranges:
            # TODO Problem could be, that select leads to duplicates in the
            # selection. So far, no problem arose. `merge` is no alternative
            # as it does not support all `commands`
            recursive_selection.select(q_index_1, q_index_2)

        super().select(recursive_selection, command)

    def _get_sub_items_index_ranges(self, q_index_parent_collection):
        """Given a collection of indexes :param: `q_index_parent_collection`,
           find the index ranges of all sub items for all indexes in the
           collection. An index range corresponds to a tuple consisting of the
           first and the last index in the range. Index ranges are used to
           describe selections effectively."""
        # `deque` is more efficient stack data structure
        q_index_parent_queue = deque(q_index_parent_collection)

        # Output queue with all index ranges found
        index_ranges = deque()
        while len(q_index_parent_queue) != 0:
            q_index_parent = q_index_parent_queue.pop()

            # Number of columns and rows of the current parent
            count_row = self.model().rowCount(q_index_parent)
            count_column = self.model().columnCount(q_index_parent)

            # If the currently processed item contains items, then the index
            # range describing these items has to be added to the output
            # `index_ranges`, and the sub items have to be processed themselves.
            # If the item has no sub items, then nothing has to be done, as its
            # own index is already included in the index range specified by
            # its own parent.
            if count_row > 0 or count_column > 0:
                # Append index range tuple to output `index_ranges`
                row = count_row - 1
                column = count_column - 1
                index_ranges.append((
                    self.model().index(0, 0, q_index_parent),
                    self.model().index(row, column, q_index_parent),
                ))
                # Append indexes of children to the queue `q_index_parent_queue`
                for row in range(count_row):
                    for column in range(count_column):
                        q_index = self.model().index(row, column,
                                                     q_index_parent)
                        q_index_parent_queue.append(q_index)

        return list(index_ranges)


class CurveView(QListView):
    delete_key = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)
        # self.setContextMenuPolicy(Qt.CustomContextMenu)
        # self.customContextMenuRequested.connect(self.show_context_menu)
        # self.context_menu = QMenu(self)
        # self.actionCalculateBD = self.context_menu.addAction('Calculate Bjontegaard-Delta')

    def keyPressEvent(self, event):
        if event.count() == 1 and event.key() == Qt.Key_Delete:
            self.delete_key.emit()

    # def show_context_menu(self, position):
    #    # unused at this point because bd is automatically calculated every time
    #    self.context_menu.exec(self.mapToGlobal(position))