from PyQt5 import QtWidgets
from PyQt5.Qt import Qt
from PyQt5.QtCore import QItemSelectionModel, QItemSelection, QModelIndex, pyqtSignal

from collections import deque
from os.path import join

import model
from SimulationDataFactory import SimulationDataItemFactory


class SimDataItemTreeView(QtWidgets.QTreeView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dragEnterEvent(self, event):
        # Consider only url/path events
        if event.mimeData().hasUrls():
            event.accept()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            self.model().update(model.SimDataItem.parse_url(url.path()))

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
                "Enocder Logs (*.log)")

            [directory, file_name] = result[0][0].rsplit('/', 1)
            return directory, file_name
        except IndexError:
            return
        else:
            # TODO usefull logging
            print("successfully added sequence")
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
        else:
            # TODO usefull logging
            print("successfully added sequence")
            return

    # adds a logfile to the treeview
    def add_sim_data_item(self):
        try:
            directory, file_name = self._get_open_file_names()
        except TypeError:
            return
        path = join(directory, file_name)
        sim_data_item = SimulationDataItemFactory.create_instance_for_file(path)
        self.model().add(sim_data_item)

    # adds a all logfiles of a sequence from a directory to the treeview
    def add_sequence(self):
        try:
            directory, file_name = self._get_open_file_names()
        except TypeError:
            return
        path = join(directory, file_name)

        sim_data_items = list(SimulationDataItemFactory.parse_directory_for_sequence(path))
        self.model().update(sim_data_items)

    # adds all logfiles and sequences from a directory to the treeview
    def add_folder(self):
        try:
            path = self._get_folder()
        except TypeError:
            return

        # TODO this uses the parse_directory method, thus, does not automatically
        # parse 'log'.subfolder. Should this be the case?
        sim_data_items = list(SimulationDataItemFactory.parse_directory(path))
        self.model().update(sim_data_items)


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
