from PyQt5 import QtWidgets
from PyQt5.Qt import Qt
from PyQt5.QtCore import QItemSelectionModel, QItemSelection, QModelIndex

from collections import deque
from os.path import join

import model


def get_top_level_items_from_tree_widget(tree_widget):
    for index in range(0, tree_widget.topLevelItemCount()):
        yield tree_widget.topLevelItem(index)

def get_child_items_from_item(item):
    return (item.child(index) for index in range(0, item.childCount()))


class View:
    def __init__(self, model=None):
        # Initialize the 'private' property for the setter to work, and
        # use setter afterwards invoking obeserver logic
        self._model = None
        self.model = model

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, model):
        if self._model is not None:
            self._model._remove_view(self)
        self._model = model
        self._model._add_view(self)

class DictTreeView(View):
    def __init__(self, tree_widget, model=None):
        super().__init__(model)
        self.widget = tree_widget

    def _update_view(self, dict_tree):
        #TODO rerender the tree is ineffective
        self.widget.clear()

        for key in dict_tree:
            child = QtWidgets.QTreeWidgetItem(None, [key])
            self.widget.addTopLevelItem(child)
            self._update_tree_widget(dict_tree[key], child)

    def _update_tree_widget(self, dict_tree, parent):
        if isinstance(dict_tree, dict) == True:
            for key in dict_tree:
                child = QtWidgets.QTreeWidgetItem(parent, [key])
                self._update_tree_widget(dict_tree[key], child)

class EncLogTreeView(QtWidgets.QTreeView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # TODO how to initialize this?
        self.value_list_model = None

        # Implement parsing of files dropped to view. Note, that the drag
        # events have to be accepted and thus, need to be reimplemented,
        # although, the elements of the view are not dragable
        self.dragEnterEvent = self.dragEnterEvent
        self.dragMoveEvent = self.dragMoveEvent
        self.dropEvent = self.dropEvent

    # is not really nice and should be fixed
    def dragEnterEvent(self, event):
        # Consider only url/path events
        if event.mimeData().hasUrls():
            event.accept()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            self.model().update( model.EncLog.parse_url( url.path() ) )

    def selectionChanged(self, q_selected, q_deselected):
        """Extend superclass behavior by automatically adding the values of
           all selected items in :param: `q_selected` to value list model. """

        for q_index in q_selected.indexes():
            # Add values, ie. data stored at the item, to the list model
            for value in q_index.internalPointer().values:
                    self.value_list_model[str(value)] = value

        for q_index in q_deselected.indexes():
            # Remove values, ie. data stored at the item, from the list model
            for value in q_index.internalPointer().values:
                    self.value_list_model.pop( str(value) )

        super().selectionChanged(q_selected, q_deselected)

    def _get_open_file_names(self):
        # extract folder and filename
        try:
            result = QtWidgets.QFileDialog.getOpenFileNames(
                self.widget,
                "Open Sequence Encoder Log",
                "/home/ient/Software/rd-plot-gui/examplLogs",
                "Enocder Logs (*.log)")

            [directory, file_name] = result[0][0].rsplit('/', 1)
            return (directory, file_name)
        except IndexError:
            return
        else:
            #TODO usefull logging
            print("successfully added sequence")
            return

    def _get_folder(self):
        # extract folder and filename
        try:
            result = QtWidgets.QFileDialog.getExistingDirectory(
                self.widget,
                "Open Sequence Encoder Log",
                "/home/ient/Software/rd-plot-gui/examplLogs")
            return result
        except IndexError:
            return
        else:
            #TODO usefull logging
            print("successfully added sequence")
            return

    # TODO Move this to controller or implement add/update at model

    def add_encoder_log(self):
        directory, file_name = self._get_open_file_names()
        path = join(directory, file_name)

        # self.model.add( model.EncLog( path ) )

    def add_sequence(self):
        directory, file_name = self._get_open_file_names()
        path = join(directory, file_name)

        encLogs = list( model.EncLog.parse_directory_for_sequence( path ) )
        # self.model.update(encLogs)

    def add_folder(self):
        path = self._get_folder()

        #TODO this uses the parse_directory method, thus, does not automatically
        # parse 'log'.subfolder. Should this be the case?
        encLogs = list( model.EncLog.parse_directory( path ) )
        # self.model.update(encLogs)

class QRecursiveSelectionModel(QItemSelectionModel):
    """Custom selection model for recursive models. If an item is selected, all
       sub items are automatically selected."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def select(self, selection, command):
        """Extend behavior of inherited method. Add all sub items to selection
           """

        # Handle selections and single indexes
        if isinstance(selection, QItemSelection):
            indexes_selected = selection.indexes()
            recursive_selection = selection
        if isinstance(selection, QModelIndex):
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
        q_index_parent_queue = deque( q_index_parent_collection )

        # Output queue with all index ranges found
        index_ranges = deque()
        while len( q_index_parent_queue ) != 0:
            q_index_parent = q_index_parent_queue.pop()
            # Get parent item from current `QModelIndex`
            parent         = q_index_parent.internalPointer()
            # Number of columns and rows of the current parent
            count_row    = self.model().rowCount(q_index_parent)
            count_column = self.model().columnCount(q_index_parent)

            # If the currently processed item contains items, then the index
            # range describing these items has to be added to the output
            # `index_ranges`, and the sub items have to be processed themselves.
            # If the item has no sub items, then nothing has to be done, as its
            # own index is already included in the index range specified by
            # its own parent.
            if count_row > 0 or count_column > 0:
                # Append index range tuple to output `index_ranges`
                row     = count_row - 1
                column  = count_column - 1
                index_ranges.append((
                    self.model().index(  0,     0, q_index_parent),
                    self.model().index(row, column, q_index_parent),
                ))
                # Append indexes of children to the queue `q_index_parent_queue`
                for row in range( count_row ):
                    for column in range( count_column ):
                        q_index = self.model().index(row, column,
                                                     q_index_parent)
                        q_index_parent_queue.append( q_index )

        return list( index_ranges )
