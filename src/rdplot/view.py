from PyQt5 import QtWidgets
from PyQt5.Qt import Qt, QApplication
from PyQt5.QtGui import QKeySequence, QKeyEvent
from PyQt5.QtCore import QObject,QItemSelectionModel, QItemSelection, QModelIndex, pyqtSignal, QThread
from PyQt5.QtWidgets import QMessageBox


from collections import deque
from os import path
from os.path import join

import model
from SimulationDataItem import SimulationDataItemFactory, SimulationDataItemError
from model import AmbiguousSimDataItems


# Path to the folder containing simulation data sub classes. The classes
# are loaded by the simulation data item factory and used for parsing files
here = path.abspath(path.dirname(__file__))
SIMULATION_DATA_ITEM_CLASSES_PATH = here + path.sep + "SimulationDataItemClasses"


class ParserWorkThread(QThread):
    newParsedData = pyqtSignal([list])

    def __init__(self, pathlist=None):
        QThread.__init__(self)

        self._factory = SimulationDataItemFactory.from_path(
            SIMULATION_DATA_ITEM_CLASSES_PATH
        )

        if pathlist is None:
            pathlist = []
        self.pathlist = pathlist

    def __del__(self):
        self.wait()

    def addPath(self,path):
        self.pathlist.append(path)

    def run(self):
        for path in self.pathlist:
            try:
                sim_data_items = self._factory.create_item_list_from_path(path)
            except SimulationDataItemError:
                self.newParsedData.emit([])
                self.pathlist.clear()
                return

            self.newParsedData.emit(sim_data_items)
        self.pathlist.clear()


class ParserWorkNoThread(QObject):
    """
    This class is intended to be used to make debugging easier,
    when breakpoints don't work because of threading
    """

    newParsedData = pyqtSignal([list])

    def __init__(self, pathlist=None):
        QObject.__init__(self)

        self._factory = SimulationDataItemFactory.from_path(
            SIMULATION_DATA_ITEM_CLASSES_PATH
        )

        if pathlist is None:
            pathlist = []
        self.pathlist = pathlist

    def addPath(self,path):
        self.pathlist.append(path)

    def run(self):
        for path in self.pathlist:
            try:
                sim_data_items = self._factory.create_item_list_from_path(path)
            except SimulationDataItemError:
                self.newParsedData.emit([])
                self.pathlist.clear()
                return

            self.newParsedData.emit(sim_data_items)
        self.pathlist.clear()

    def start(self):
        self.run()


class SimDataItemTreeView(QtWidgets.QTreeView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parserThread = ParserWorkThread()
        # helpful for debugging, when breakpoints don't work because of threading
        # self.parserThread = ParserWorkNoThread()
        self.parserThread.newParsedData.connect(self._update_model)
        self.msg = QMessageBox(self) # use self as parent here
        self.msg.setIcon(QMessageBox.Information)
        self.msg.setText("Parsing Directory...")
        self.msg.setWindowTitle("Info")

    def dragEnterEvent(self, event):
        # Consider only url/path events
        if event.mimeData().hasUrls():
            event.accept()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            self.msg.show()
            self.parserThread.addPath( url.path() )
            self.parserThread.start()

    # Keypress fix from
    # http://stackoverflow.com/questions/27475940/pyqt-connect-to-keypressevent

    deleteKey = pyqtSignal()

    def keyPressEvent(self, q_key_event):
        if q_key_event.count() == 1 and q_key_event.key() == Qt.Key_Delete:
            self.deleteKey.emit()
        super().keyPressEvent(q_key_event)

    def _get_open_file_names(self):
        # extract folder and filename
        try:
            result = QtWidgets.QFileDialog.getOpenFileNames(
                self,
                "Open Sequence Encoder Log",
                "/home/ient/Software/rd-plot-gui/examplLogs",
                "All Logs (*.log *.xml);;Enocder Logs (*.log);;Dat Logs (*.xml)")

            [directory, file_name] = result[0][0].rsplit('/', 1)
            return directory, file_name
        except IndexError:
            return

    def _get_folder(self):
        # extract folder and filename
        try:
            result = QtWidgets.QFileDialog.getExistingDirectory(
                self,
                "Open Directory",
                "/home/ient/Software/rd-plot-gui/examplLogs")
            return result
        except IndexError:
            return

    # adds a logfile to the treeview
    def add_sim_data_item(self):
        try:
            directory, file_name = self._get_open_file_names()
        except TypeError:
            return
        path = join(directory, file_name)
        self.parserThread.addPath(path)
        self.parserThread.start()

    # adds all logfiles and sequences from a directory to the treeview
    def add_folder(self):
        try:
            path = self._get_folder()
        except TypeError:
            return

        # TODO this uses the parse_directory method, thus, does not automatically
        # parse 'log'.subfolder. Should this be the case?
        #sim_data_items = list(SimulationDataItemFactory.parse_directory(path))
        #self.model().update(sim_data_items)
        self.msg.show()
        self.parserThread.addPath(path)
        self.parserThread.start()

    def _update_model(self,sim_data_items):
        self.msg.hide()
        if not sim_data_items:
            msg = QMessageBox(self)  # use self as parent here
            msg.setIcon(QMessageBox.Information)
            msg.setText("I cannot find any simulation data item in your selected directory.\n"
                        "If you are really sure that there should be some valid item, "
                        "you should consider writing a new parser.")
            msg.setWindowTitle("Info")
            msg.show()
        try:
            self.model().update(sim_data_items)
        except AmbiguousSimDataItems:
            msg = QMessageBox(self)  # use self as parent here
            msg.setIcon(QMessageBox.Warning)
            msg.setText("I have found ambigous simualtion data items in your selected directory.\n"
                        "The reason for that is that you want to parse files from one directory "
                        "with different names but the same QP and sequence name.\n"
                        "From all the parsers I know at the moment I cannot decide what you want "
                        "to achieve.\n"
                        "Recommendation: Move the files you do not want plot to a different location.\n"
                        "Note: The sequence tree view on the left is most probably incomplete now.")
            msg.setWindowTitle("Warning")
            msg.show()


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
            # selection. So far, no problem arised. `merge` is no alternative
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
            # Get parent item from current `QModelIndex`
            parent = q_index_parent.internalPointer()
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
