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
from collections import deque
from os.path import sep
from os import environ
import numpy as np
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QPushButton
from PyQt5.Qt import Qt, QVariant, QModelIndex, QDialog, QHBoxLayout, QVBoxLayout, QAbstractItemView, QMessageBox

from PyQt5.QtCore import QAbstractListModel, QAbstractItemModel, QAbstractTableModel, pyqtSignal, QObject
from PyQt5.QtGui import QBrush

import matplotlib.pyplot as plt
from rdplot.SimulationDataItemClasses.EncoderLogs import AbstractEncLog
from rdplot.lib.BD import bjontegaard
from string import Template
from tabulate import tabulate
import pkg_resources


#
# Functions
#

def compare_strings_case_insensitive(first, second):
    return first.casefold() > second.casefold()


# -------------------------------------------------------------------------------


#
# Models
#
class ModelError(Exception):
    """Error class for model"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AmbiguousSimDataItems(ModelError):
    """Error class for ambiguous sim data items"""
    pass


# noinspection PyMethodOverriding
class OrderedDictModel(QAbstractListModel):
    """Subclass of :class: `QAbstractListModel` implementing an
    :class: `OrderedDict`, whose keys are also the items of the qt list. If
    used with a :class: `QListView`, the keys are displayed.

    :param *args:    All args forwarded to parent class
    :param **kwargs: All keyword args forwarded to parent class

    Implements the *items_changed* signal, which is emitted on change of the
    keys/items. If used with the methods :func: `update_from_tuples`, :func:
    `clear_and_update_from_tuples` or :func: `remove_keys` it is especially
    efficient, as it allows updating the model with a collection of
    keys/items, but emitting the *items_changed* signal only once.
    """

    items_changed = pyqtSignal()

    def __init__(self, *args, compare_keys_function=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Function to compare keys. This function defines the order of the keys
        if compare_keys_function is None:
            def compare_keys_function(first, second):
                return first > second
        self._compare_keys_function = compare_keys_function

        self._keys = []
        self._items = []

    # Qt interface methods

    def rowCount(self, parent):
        return len(self)

    def data(self, q_index, role):
        if q_index.isValid() and role == Qt.DisplayRole:
            for index, (key, item) in enumerate(self.items()):
                if index == q_index.row():
                    return QVariant(key)
        return QVariant()

    # Reimplemented dictionary methods.
    # Note, that implementation of __setitem__ and pop is done using
    # custom methods, so that *items_changed* is emitted correctly.

    def __getitem__(self, key):
        return self._items[self._keys.index(key)]

    def __setitem__(self, key, item):
        self.update((key, item))

    def pop(self, key):
        item = self[key]
        self.remove_keys([key])
        return item

    def __iter__(self):
        return iter(self._keys)

    def __contains__(self, key):
        return key in self._keys

    def __len__(self):
        return len(self._keys)

    def __str__(self):
        return str(list(self._keys))

    def __repr__(self):
        return str(self)

    def values(self):
        return list(self._items)

    def items(self):
        return list(zip(self._keys, self._items))

    # Implement specific methods
    # Note, that these methods allow update of whole ranges of data and emit
    # the *items_changed* signal afterwards. This allows more efficient update
    # behavior.

    def update_from_tuples(self, tuples):
        """Add/replace items to the dictionary specified in the iterable :param:
        *tuples* of (key, item) pairs. Emit *items_changed* afterwards.
        """

        for key, item in tuples:
            # If the key is already present, just update its item and continue
            if key in self:
                self._items[self._keys.index(key)] = item
                continue

            # Else search the insertion position by comparision
            index_insert = len(self)
            for index, key_other in enumerate(self):
                # If the key is bigger, then insert key/item here
                if self._compare_keys_function(key_other, key):
                    index_insert = index
                    break

            # Call Qt interface functions and add/replace item corresponding
            # to key
            self.beginInsertRows(QModelIndex(), index_insert, index_insert + 1)
            self._keys.insert(index_insert, key)
            self._items.insert(index_insert, item)
            self.endInsertRows()

        self.items_changed.emit()

    def clear_and_update_from_tuples(self, tuples):
        """Clear the dictionary and update it the (key, item) pairs specified
        in *tuples*. Emit *items_changed* afterwards.

        :param tuples: Iterable of tuples of (key, item) which are added
            to the dictionary."""

        # Call Qt interface functions and remove all keys and corresponding
        # items from the dictionary
        self.beginRemoveRows(QModelIndex(), 0, len(self) - 1)
        self._keys.clear()
        self._items.clear()
        self.endRemoveRows()

        # Update it with (key, item) pairs specified by *tuples*. The update
        # method emits *items_changed*.
        self.update_from_tuples(tuples)

    def remove_keys(self, keys):
        """Remove all keys and corresponding items specified in iterable
        from dictionary. Emit *items_changed* afterwards.

        :param keys: *keys* which are removed from dictionary together with
            the corresponding items
        """

        # Iterate to find index corresponding to key in ordered dict
        for key in keys:
            for index, key_other in enumerate(self):
                if key_other == key:
                    break

            # Call Qt interface functions and remove key and corresponding item
            self.beginRemoveRows(QModelIndex(), index, index + 1)
            self._keys.pop(index)
            self._items.pop(index)
            self.endRemoveRows()

        self.items_changed.emit()


# Tree model OrderedDictTreeModel is subclass of QAbstractItemModel class,
# and implements the abstract methods, thus, the model valid for Qt QTreeView.
# The OrderedDictTreeItem class implements items of the tree model.
# Implementation was done according to the example at
# http://doc.qt.io/qt-5/qtwidgets-itemviews-simpletreemodel-example.html
# and corresponding files under BSD licence.


class OrderedDictTreeItem(QObject):
    """Item of :class: `OrderedDictTreeModel`. The item imitates the
    behavior of a dictionary, thus, the children of an item can be accessed
    using slice notation and their identifiers, eg.:

    >>> parent['child_identifier']

    In contrast to that, slice assignment is **not** supported. This
    would not be very useful, as the key to an item is **always** its
    identifier, thus, an *item* is always assigned to its *identifier* as
    key. Therefore, the functions for appending children are named as with
    sets, ie. :func: `_add` for single items and :func: `_update` for
    iterables of items. Additional some dictionary operators are supported.

    The :func: `_add`, :func: `_update` and :func: `_remove` are marked
    private, as they should only be called from the :class:
    `OrderedDictModel` object, as the qt tree indexes have to be updated
    accordingly.

    The *values* property corresponds to some set of data.

    :param identifier: Unique/hashable identifier of the item. The item is
        referenced from the parent item by using this identifier.
    :param parent: Parent item
    :param children: Iterable of children of the item
    :param values: Values contained by the item
    :param identifier_compare_function: Function to compare two identifiers,
        defines the order of children.
    """

    def __init__(self, identifier=None, parent=None, children=None,
                 values=None, compare_identifiers_function=None):
        super().__init__()
        self._identifier = identifier
        self._parent = parent

        self._children = []
        if children is not None:
            self.extend(children)

        self.values = set() if values is None else values

        if compare_identifiers_function is None:
            def compare_identifiers_function(first, second):
                return first > second
        self._compare_identifiers_function = compare_identifiers_function

    # Properties for private attributes

    @property
    def identifier(self):
        return self._identifier

    @property
    def parent(self):
        return self._parent

    @property
    def children(self):
        # Copy the list of children
        return list(self._children)

    # Special functions/properties

    @property
    def leafs(self):
        """Walk all items below the item in the tree and return all leafs ie.
        items which do not have any children themselves.

        :rtype: `list` of :class: `OrderedDictTreeItem`s
        """

        items = deque([self])

        leafs = deque()
        while len(items) != 0:
            item = items.pop()

            items.extend(item.children)
            if len(item) == 0:
                leafs.append(item)

        return list(leafs)

    @property
    def dict_tree(self):
        """Walk all items below item in the tree and convert to a tree of
        dictionaries. For leaf items the value set is returned.

        :rtype: :class: `dict` with *identifiers* as keys and recursive call to
            :func: `dict_tree` as item
        :rtype: :class: `set` of values
        """

        if len(self) == 0:
            return self.values
        return {identifier: self[identifier].dict_tree for identifier in self}

    @property
    def path(self):
        """Walk up the path up until the root item and return list of all passed
        items.

        :rtype: :class: `list` of :class: `OrderedDictTreeItem`
        """

        path = deque([self])
        item = self
        while item.parent is not None:
            path.appendleft(item.parent)
            item = item.parent

        return list(path)

    # Functions to add/remove children of the item

    def _add(self, child):
        child._parent = self

        # Find the insertion index of the child, and do insertion.
        for index, identifier in enumerate(self):
            # If child is already present overwrite it
            if identifier == child.identifier:
                self._children[index] = child
                return
            # If the identifier is bigger than the current one, and thus,
            # all identifiers before, do insertion here
            if self._compare_identifiers_function(identifier, child.identifier):
                self._children.insert(index, child)
                return

        # If no position has been found, just append the element
        self._children.append(child)

    def _update(self, children):
        for child in children:
            self.add(child)

    def _remove(self, child):
        child._parent = None
        self._children.remove(child)

    # Reimplemented some dictionary functions

    def __getitem__(self, identifier):
        """Get child by *identifier*"""

        for child in self._children:
            if child.identifier == identifier:
                return child

        raise KeyError("Key {key} not found in item {item}".format(
            key=identifier,
            item=str(self)
        ))

    def __len__(self):
        """Number of children"""
        return len(self._children)

    def __iter__(self):
        """Iterate over *identifier*s ie. dictionary keys"""
        for child in self._children:
            yield child.identifier

    def __contains(self, identifier):
        """Check for identifier ie. key in *children*"""
        for identifier_child in self:
            if identifier_child == identifier:
                return True
        return False

    def __str__(self):
        return str(self.identifier)

    def __repr__(self):
        """Display item as dictionary tree"""
        return str(self.dict_tree)


# noinspection PyMethodOverriding
class OrderedDictTreeModel(QAbstractItemModel):
    def __init__(self, *args, default_item_values=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Default item values
        if default_item_values is None:
            default_item_values = set()
        self._default_item_values = default_item_values

        self._root = OrderedDictTreeItem(
            values=self._default_item_values,
            compare_identifiers_function=compare_strings_case_insensitive
        )

    # Properties

    @property
    def root(self):
        return self._root

    # Qt interface functions implemented according to
    # http://doc.qt.io/qt-5/qtwidgets-itemviews-simpletreemodel-example.html

    def index(self, row, column, q_parent_index):
        if not self.hasIndex(row, column, q_parent_index):
            return QModelIndex()
        if q_parent_index.isValid():
            item = q_parent_index.internalPointer().children[row]
            return self.createIndex(row, 0, item)
        return self.createIndex(row, column, self.root.children[row])

    def parent(self, q_parent_index):
        if q_parent_index.isValid():
            parent = q_parent_index.internalPointer().parent
            if parent != self.root:
                row = parent.parent.children.index(parent)
                return self.createIndex(row, 0, parent)
        return QModelIndex()

    def rowCount(self, q_parent_index):
        # TODO Handle different column values
        if q_parent_index.isValid():
            return len(q_parent_index.internalPointer())
        return len(self.root)

    def columnCount(self, q_parent_index):
        # All items only hold their own identifier as data to be displayed,
        # thus, the argument is irrelevant
        return 1

    def data(self, q_parent_index=QModelIndex(), q_role=Qt.DisplayRole):
        if q_parent_index.isValid():
            if q_role == Qt.DisplayRole:
                siblings = q_parent_index.internalPointer().parent.children
                if len(siblings) > 1:
                    sibling_identifiers = []
                    sibling_identifiers += [sibling.identifier.split(sep) for sibling in siblings]
                    unique_part = []
                    for c in sibling_identifiers:
                        result = list(filter(lambda x: all(x in l for l in sibling_identifiers) == False, c))
                        unique_part.append(" ".join(result))

                    return unique_part[q_parent_index.row()]
                else:
                    path = str(q_parent_index.internalPointer())
                    return path
            elif q_role == Qt.ForegroundRole:
                if q_parent_index.internalPointer().property('needs_reload') == 'True':
                    # color items in gray for visibility
                    # final color still up for debate
                    # todo set color in settings
                    return QBrush(Qt.gray)
        return QVariant()

    # Non-Qt interface functions

    def get_item_from_path(self, *path):
        # Save the leaf item to a variable in the current closure, so it can
        # be retrieved from *_walk_path* and then be returned
        # Note, that this needs to be a list, so closure is supported
        leaf_item = []

        def function_leaf_item(item_parent, q_index_parent):
            leaf_item.append(item_parent)

        # Raise an error, if an item of the path does not exist
        def function_item_not_existing(key, item_parent, q_index_parent):
            raise KeyError("Key {} does not exist on path {}".format(
                key,
                path
            ))

        # Walk the path and return the leaf item
        self._walk_path(
            *path,
            function_item_not_existing=function_item_not_existing,
            function_leaf_item=function_leaf_item
        )
        return leaf_item[0]

    def create_path(self, *path):
        """Create all items along *path* if they are not already present. Return
        last *item* of the path.

        :param *path: Accepts an arbitrary number of *identifiers* as path

        :rtype: Leaf :class: `OrderedDictTreeItem` item of the created path
        """

        # Callback, which is used to create items not already present at the
        # *path*
        def create_item(key, item_parent, q_index_parent):
            # Always add as last child
            row = len(item_parent)
            for index, identifier in enumerate(item_parent):
                if compare_strings_case_insensitive(key, identifier):
                    row = index
                    break
            # Call Qt update functions
            self.beginInsertRows(q_index_parent, row, row)
            item = OrderedDictTreeItem(
                identifier=key,
                values=self._default_item_values.copy(),
                compare_identifiers_function=compare_strings_case_insensitive
            )
            item_parent._add(item)
            self.endInsertRows()

        # Save the leaf item to a variable in the current closure, so it can
        # be retrieved from *_walk_path* and then be returned
        # Note, that this needs to be a list, so closure is supported
        leaf_item = []

        def function_leaf_item(item_parent, q_index_parent):
            leaf_item.append(item_parent)

        # Use the walk path function  and return the leaf item afterwards:
        #   * Create items if they do not exist on the specified  *path*
        #   * Save the leaf item of the path, so it can be returned
        self._walk_path(
            *path,
            function_item_not_existing=create_item,
            function_leaf_item=function_leaf_item
        )
        return leaf_item[0]

    def _walk_path(self, *path, function_item_not_existing=None,
                   function_leaf_item=None):
        """Generalization of path walking, which supports callback functions
        if an item of the *path* is not present and for the leaf item of the
        *path*. Retrieving the leaf item and creation of paths are implemented
        using this function.

        :param *path: :class: `list` of identifiers which correspond to a path
            of the tree
        :param function_item_not_existing: Function, which is called if
            an identifier of *path* is not present at the tree with arguments:
                * the current key/identifier
                * the current parent item :class: `OrderedDictTreeItem`
                * its parent index :class: `QModelIndex`
        :param function_leaf_item: Function which is called after the path walk
            is finished, with the arguments:
                * leaf item :class: `OrderedDictTreeItem`
                * its index :class: `QModelIndex`
        """

        # Each path starts at root item *item_parent* and root *q_index_parent*
        item_parent = self.root
        q_index_parent = QModelIndex()

        # Walk the path
        for index, key in enumerate(path):
            # Set the current item as *item_parent* for next iteration, and
            # update the *q_index_parent* accordingly
            if key not in item_parent:
                if function_item_not_existing is not None:
                    function_item_not_existing(key, item_parent,
                                               q_index_parent)
            item_parent = item_parent[key]
            row = self._get_row_from_item_and_index_parent(
                item_parent,
                q_index_parent,
            )
            q_index_parent = self.index(row, 0, q_index_parent)

        # Note, that *item_parent* is now the last item specified by path
        if function_leaf_item is not None:
            function_leaf_item(item_parent, q_index_parent)

    def _get_index_parent_from_item(self, item):
        """Get the :class: `QModelIndex` *q_parent_index* of the parent item of
        *item*. Note, that the tree has to walked up and down again
        to find the index, so performance depends on the depth of the tree.

        :param item: The parent index of this item is found.

        :rtype: :class: `QModelIndex*
        """

        # Return invalid index if *item* is the root item
        if item.parent is None:
            return QModelIndex()

        # Walk the tree up the chain of parent items until the root item
        # to find the *path*
        path_queue = deque()
        other = item.parent
        while True:
            path_queue.appendleft(other)
            # Break if *other* is the root item
            if other.parent is None:
                break
            other = other.parent
        path = list(path_queue)

        # Walk the path down again to the *item* and create
        # QModelIndex along the way.
        q_index_parent = QModelIndex()
        for (parent, item) in zip(path[:-1], path[1:]):
            row = parent.children.index(item)
            q_index_parent = self.index(row, 0, q_index_parent)

        return q_index_parent

    def _get_index_from_item(self, item):
        """Get the :class: `QModelIndex` corresponding to a given *item*.

        :param item: :class: `OrderedDictTreeItem`

        :rtype: :class: `QModelIndex` corresponding to the *item*
        """

        # If the **item** itself is the root item, return an invalid index
        if item.parent is None:
            return QModelIndex()

        q_index_parent = self._get_index_parent_from_item(item)

        # If the **parent** item is not the root item, create the index
        # corresponding to *item* and return it.
        if q_index_parent.isValid():
            row = q_index_parent.internalPointer().children.index(item)
            return self.index(row, 0, q_index_parent)

        # If the **parent** item is the root item, create index and return it.
        row = self.root.children.index(item)
        return self.index(row, 0, QModelIndex())

    def _get_row_from_item_and_index_parent(self, item, q_index_parent):
        """Get the row of an *item* in reference to its parent at
        *q_parent_index*.

        :param item: Get the position of :class: `OrderedDictTreeItem`
        :param q_index_parent: :class: `QModelIndex` of the parent of *item*

        :rtype: :class: `Int`
        """

        if q_index_parent.isValid():
            return q_index_parent.internalPointer().children.index(item)
        # If the *q_index_parent* is invalid, default to root being
        # parent
        return self.root.children.index(item)

    def remove_item(self, item, q_index_parent=None):
        """Remove *item* from the tree. Additionally to the item itself, all sub
        items are removed. Also, all items above *item* in the tree are removed,
        if they do not have any other children, do not contain any values and
        are not the root item. Note, that due to these additional procedures,
        which have to be done, removal of an item requires some performance.

        :param item: Item to be removed :class: `OrderedDictTreeItem`
        :param q_index_parent: :class: `QModelIndex` of the parent of *item*
        """

        # If the parent index is not known, look it up
        if q_index_parent is None:
            q_index_parent = self._get_index_parent_from_item(item)

        # Get the row position of the *item* relative to its parent
        row = self._get_row_from_item_and_index_parent(item, q_index_parent)

        # Before removing *item* itself, recursively remove all sub items, if
        # there are any
        if len(item) > 0:
            q_index = self.index(row, 0, q_index_parent)
            for child in item:
                self.remove_item(item[child], q_index)

        parent = item.parent

        if parent:  # todo: this check is necessary. fixing a bug. Still, how can parent be None?
            # Remove *item* itself and notify view
            self.beginRemoveRows(q_index_parent, row, row)
            parent._remove(item)
            self.endRemoveRows()

            # Remove parent item recursively if
            # * the parent item has no children
            # * the parent item does not contain any values
            # * the parent item is not the root item
            condition = (
                len(parent) == 0
                and len(parent.values) == 0
                and parent.parent is not None
            )
            if condition:
                self.remove_item(parent, self.parent(q_index_parent))

    def clear(self):
        """Remove all items except the *root* item from the tree."""

        for child in self.root:
            self.remove_item(self.root[child], QModelIndex())

    def __repr__(self):
        return str(self.root.dict_tree)


class SimDataItemTreeModel(OrderedDictTreeModel):
    """Tree model specific to sim data items, specifying methods to add them to
    the tree, how to store their data at the tree and how to access them, using
    the tree. Implements *item_changed* signal, which is emitted after the
    tree model has been altered. With :func: `add`, :func: `update` and :func:
    `remove`, the signal allows altering a collection of items and efficiently
    updating the GUI, as *item_changed* is emitted, after all model alterations
    have been processed.

    :param *args:    Pass to superclass
    :param **kwargs: Pass to superclass
    """

    items_changed = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dialog = AttributesDialog()

    # Implement *add*, *update* and remove to add/remove sim data items to the
    # tree.
    # Note, that *add* is implemented using update, so *items_changed* is
    # emitted efficiently.

    def add(self, sim_data_item):
        """Like update, but for a single *sim_data_item*. *items_changed* is issued
        by calling :func: `update` .

        :param sim_data_item: :class: `SimDataItem` to be added to tree
        """
        self.update([sim_data_item])

    def update(self, sim_data_items, check_add_param = True):
        """Adds all elements in the iterable *sim_data_items* to the tree or
        replaces them if they are already present. Issues the *items_changed*
        signal, after all sim data items are added/replaced.

        :param sim_data_items: Iterable collection of :class: `SimDataItem`s to be added

        """
        additional_param_found = []
        all_log_configs = {}
        diff_dict = {}

        # build up a diff dict in order let the software handle multiple configuration parameters
        # in one simulation directory
        # some of the diffs should not be interpreted as parameters
        # those are removed from the dict; for sure QP, RealFormat, InternalFormat, and Warning
        # are not parameters
        # if you want to simulate with your own parameters, make sure that they appear in the
        # logfile
        try:
            self.dialog.chosen_par.clear()
            self.dialog.not_chosen_par.clear()
            self.dialog.reset = True
            QP_added = False
            for sim_data_item in sim_data_items:
                if sim_data_item.__class__ not in all_log_configs:
                    all_log_configs[sim_data_item.__class__] = []
                    diff_dict[sim_data_item.__class__] = {}
                all_log_configs[sim_data_item.__class__].append(sim_data_item.log_config)
                # create list for all configuration parameters of the simulation_data_item
                # this configuration parameters will be displayed in the VariableTreeModel
                # If a qp parameter is available, we keep it as default in the List.
                # If the qp parameter is the only element in diff_dict or
                # if the user opens single files and not a directory,
                # no dialog window will be opened where you could add/remove all configuration parameters
                # that differ between the sim_data_items
                # TODO: enable multiple configuration parameters for the case that a specific file is opened
                if hasattr(sim_data_item, 'qp') and not QP_added:
                    self.dialog.chosen_par.addItems(['QP'])
                    QP_added = True
                # print(sim_data_item.summary_data['encoder_config'])
            value_filter = ['.yuv', '.bin', '.hevc', '.jem']
            key_filter = []
            for sim_class in all_log_configs.keys():
                for i in range(len(all_log_configs[sim_class]) - 1):
                    current_item, next_item = all_log_configs[sim_class][i], all_log_configs[sim_class][i + 1]
                    for (key, value) in set(current_item.items()) ^ set(next_item.items()):
                        if all(y not in key for y in key_filter):
                            if all(x not in value for x in value_filter):
                                if key not in diff_dict[sim_class]:
                                    diff_dict[sim_class][key] = []
                                    diff_dict[sim_class][key].append(value)
                                else:
                                    if value not in diff_dict[sim_class][key]:
                                        diff_dict[sim_class][key].append(value)

                # dialog window which displays all parameters with varying values in a list
                # the user can drag the parameters, he wants to analyse further into an other list
                # the order of the parameters in the list determines the order of the parameter tree
                if diff_dict[sim_class]:
                    self.dialog.not_chosen_par.addItems([item for item in diff_dict[sim_class] if item != 'QP'])
                    if self.dialog.not_chosen_par:
                        self.dialog.exec_()
                    for i in range(len(self.dialog.not_chosen_par)):
                        diff_dict[sim_class].pop(self.dialog.not_chosen_par.item(i).text(), None)
                additional_param_found.append(sim_class)

        except AttributeError:
            # maybe do something useful here
            # This is for conformance with rd data written out by older versions of rdplot
            pass

        for sim_data_item in sim_data_items:

            has_additional_params = False
            if sim_data_item.__class__ in additional_param_found:
                sim_data_item.additional_params = [self.dialog.chosen_par.item(i).text() for i in range(len(self.dialog.chosen_par))]
                has_additional_params = True

            # Get *item* of the tree corresponding to *sim_data_item*
            item = self.create_path(*sim_data_item.tree_identifier_list)

            # This prevents an sim data item overwriting another one
            # with same *tree_identifier_list* but different absolute path
            for value in item.values:
                condition = (
                    value.tree_identifier_list == sim_data_item.tree_identifier_list
                    and value.path != sim_data_item.path
                    and not has_additional_params
                    and check_add_param
                )
                if condition:
                    raise AmbiguousSimDataItems((
                                                    "Ambiguous sim data items: Sim Data Item {} and {}"
                                                    " have different absolute paths but the same"
                                                    " position at the tree {}"
                                                ).format(sim_data_item, value, AbstractEncLog.tree_identifier_list))
            # Add *sim_data_item* to the set of values of the tree item *item*
            item.values.add(sim_data_item)

        self.items_changed.emit()

    def remove(self, sim_data_items):
        """Remove all elements in iterable collection *sim_data_items* from the tree.
        Emit *items_changed* signal after all sim data items are removed.

        :param sim_data_items: Iterable collection of :class: `SimDataItem`s to be removed
        """
        for sim_data_item in sim_data_items:
            # Get *item* of the tree corresponding to *sim_data_item*
            item = self.create_path(*sim_data_item.tree_identifier_list)
            self.remove_item(item)

        self.items_changed.emit()


class VariableTreeModel(OrderedDictTreeModel):
    """Tree model to store the parsed data, which corresponds to the currently
    selected sim data items. The data is stored in lists at the leafs of the tree.
    The tree itself corresponds to a structure of variables, which is exported
    by the sim data items. The model implements the *item_changed* signal to
    be compatible to the :class: `QRecursiveSelectionModel` class.
    """

    items_changed = pyqtSignal()

    def __init__(self, *args, **kwargs):
        # Use lists as default item value
        super().__init__(*args, default_item_values=[], **kwargs)

    def update_from_dict_tree(self, dict_tree):
        """ Update the tree from *dict_tree* . Keys create tree items, and the
        leafs of the dictionary tree are appended as values to the corresponding
        tree items.

        :param dict_tree: tree of nested :class: `dict`s
        """

        pairs = deque(([key], item) for (key, item) in dict_tree.items())
        while len(pairs) != 0:
            (path, item) = pairs.pop()

            if isinstance(item, dict):
                pairs.extend(
                    (path + [key], item) for key, item in item.items()
                )
                continue

            tree_item = self.create_path(*path)
            tree_item.values.extend(item)

        self.items_changed.emit()

    def clear_and_update_from_dict_tree(self, dict_tree):
        # TODO This needs to be called two times, what obviously should not
        # be the case
        self.clear()
        self.clear()
        self.update_from_dict_tree(dict_tree)


# This is the model for storing the bd table
# noinspection PyMethodOverriding
class BdTableModel(QAbstractTableModel):
    def __init__(self, parent=None, *args):
        super(BdTableModel, self).__init__()
        self._data = np.empty(shape=[0, 0])
        self._horizontal_headers = []
        self._vertical_headers = []

        # Store the current anchor index and plot data collection
        self._anchor_index = 0
        self._plot_data_collection = []

    def rowCount(self, parent):
        return self._data.shape[0]

    def columnCount(self, parent):
        return self._data.shape[1]

    def data(self, q_index, role):
        if q_index.isValid() and role == Qt.DisplayRole:
            value = self._data[q_index.row(), q_index.column()]
            return QVariant(str(value))
        return QVariant()

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            tmp_horizontal_headers = [header.split(sep) for header in self._horizontal_headers]
            headers = []
            for c in tmp_horizontal_headers:
                result = list(filter(lambda x: all(x in l for l in tmp_horizontal_headers) == False, c))
                headers.append(" ".join(result))
            return QVariant(headers[col])
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return QVariant(self._vertical_headers[col])
        return QVariant()

    def flags(self, index):
        return Qt.ItemIsEnabled

    def reset_model(self):
        self.beginRemoveColumns(QModelIndex(), 0, self._data.shape[1])
        self.removeColumns(0, self._data.shape[1], QModelIndex())
        self.endRemoveColumns()

        self.beginRemoveRows(QModelIndex(), 0, self._data.shape[0])
        self.removeRows(0, self._data.shape[0], QModelIndex())
        self.endRemoveRows()

        self._data = np.empty(shape=[0, 0])
        self._horizontal_headers = []
        self._vertical_headers = []
        self.headerDataChanged.emit(Qt.Horizontal, 0, self._data.shape[1])
        self.headerDataChanged.emit(Qt.Vertical, 0, self._data.shape[0])

        if plt.get_fignums():
            plt.cla()

    def update(self, plot_data_collection, bd_option, interp_option, bd_plot):
        # reset the model in the first place and set data afterwards appropriately
        self.beginResetModel()
        self.reset_model()
        self.endResetModel()

        # there is no need to calculate a bd for just one curve
        if len(plot_data_collection) < 2:
            plt.close()
            return

        seq_set = set()
        config_set = set()
        identifier_list = []
        for i in plot_data_collection:
            # there is no reason for calculating a bjontegaard, if we want to plot
            # several variables from the same sequence and config, so return in that case
            # otherwise append the identifiers to the list and go on
            if identifier_list.__contains__(i.identifiers):
                return
            identifier_list.append(i.identifiers)

            seq_set.add(i.identifiers[0])
            config_set.add('+'.join(i.identifiers[1:]))
        seq_set = sorted(seq_set)
        config_set = sorted(config_set)

        if len(seq_set) > 1:
            plt.close()
            bd_plot = True

        # there is no need to calculate a bjontegaard delta, if only one configuration is loaded
        if len(config_set) < 2:
            plt.close()
            return
        elif len(config_set) > 5 and (not bd_plot):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("Your BD plot will contain more than 5 curves, do you really want to continue?")
            msg.setWindowTitle("Info")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            result = msg.exec()

            if result == QMessageBox.Cancel:
                plt.close()
                bd_plot = True

        self._horizontal_headers = list(config_set)
        self._vertical_headers = list(seq_set)
        self._vertical_headers.append('AVG')

        # insert as many columns as we need for the selected data
        self.beginInsertColumns(QModelIndex(), 0, len(config_set) - 1)
        self.insertColumns(0, len(config_set), QModelIndex())
        self.endInsertColumns()

        # insert as many rows as we need for the selected data
        # and add one row for the average
        self.beginInsertRows(QModelIndex(), 0, len(seq_set))
        self.insertRows(0, len(seq_set), QModelIndex())
        self.endInsertRows()

        self._plot_data_collection = plot_data_collection

        self._data = np.zeros((len(seq_set) + 1, len(config_set)))
        allowed_units = [("kbps","dB"),("kbps","s"),("kbps","VMAFScore")]
        if all(collection.label in allowed_units for collection in plot_data_collection):
            self.update_table(bd_option, interp_option, 0, bd_plot)
        else:
            self.beginResetModel()
            self.reset_model()
            self.endResetModel()
            plt.close()

    # This function is called when the anchor, the interpolation method
    # or the output of the bjontegaard delta is changed
    def update_table(self, bd_option, interp_option, anchor_index, bd_plot):
        # if there are no rows and columns in the model,
        # nothing can be updated
        if bd_plot:
            plt.close()
        elif (not bd_plot) and len(self._horizontal_headers) > 5:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("Your BD plot will contain more than 5 curves, do you really want to continue?")
            msg.setWindowTitle("Info")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            result = msg.exec()

            if result == QMessageBox.Cancel:
                plt.close()
                bd_plot = True

        if self.rowCount(self) == 0 and self.columnCount(self) == 0:
            return

        # set the whole data matrix to zero first
        self._data = np.zeros((len(self._vertical_headers), len(self._horizontal_headers)))

        # if we have passed the index of the column for the anchor select that one as anchor
        try:
            anchor = self._horizontal_headers[self._anchor_index]
        except:
            anchor_index = 0
        if isinstance(anchor_index, int) and anchor_index != -1:
            if (self._anchor_index != anchor_index) and not bd_plot:
                plt.clf()
            anchor = self._horizontal_headers[anchor_index]
            self._anchor_index = anchor_index

        # iterate over all rows (sequences) and columns (configurations)
        # of the table. Calculate one bd for each cell and store it in the
        # model. Emit in the very end the dataChanged signal
        row = 0
        anchor_row = [x.identifiers[0] for x in self._plot_data_collection if x.identifiers[1] == anchor][0]
        for seq in self._vertical_headers:
            # the AVG seq is actually not a sequence, so just skip it
            if seq == 'AVG':
                continue
            col = 0
            for config in self._horizontal_headers:
                # for the anchor vs anchor measurement the bd is zero,
                # so just skip that case
                if config == anchor:
                    col += 1
                    continue
                # determine the identifiers of the current cell
                identifiers_tmp = [seq, config]

                # if the anchor configuration is not available for the current seq continue
                if len([x for x in self._plot_data_collection if
                        '+'.join(x.identifiers).__eq__('+'.join([identifiers_tmp[0], anchor]))]) == 0:
                    self._data[row, col] = np.nan
                    col += 1
                    continue

                # get the rd values for curve c1 which is the anchor
                c1 = [x for x in self._plot_data_collection if
                      '+'.join(x.identifiers).__eq__('+'.join([identifiers_tmp[0], anchor]))][0].values
                c1 = sorted(list(set(c1)))  # remove duplicates, this is just a workaround for the moment....

                # if the configuration is not available for the current seq continue
                if len([x for x in self._plot_data_collection if
                        '+'.join(x.identifiers).__eq__('+'.join(identifiers_tmp))]) == 0:
                    self._data[row, col] = np.nan
                    col += 1
                    continue

                # get the rd values for curve c2
                c2 = [x for x in self._plot_data_collection
                      if '+'.join(x.identifiers).__eq__('+'.join(identifiers_tmp))][0].values
                c2 = sorted(list(set(c2)))

                # if a simulation does not contain at least 4 rate points,
                # we do not want to calculate the bd
                if len(c1) < 4 or len(c2) < 4:
                    self._data[row, col] = np.nan
                    col += 1
                    continue

                # calculate the bd, actually this can be extended by some plots
                configs = [anchor, identifiers_tmp[1]]
                self._data[row, col] = bjontegaard(c1, c2, bd_option, interp_option, 'BD Plot ' + seq, configs, bd_plot)
                col += 1
            row += 1

        # calculate the AVG rate savings or delta psnr and round the output to something meaningful
        self._data[row, :] = np.mean(self._data[:-1, :][~np.isnan(self._data[:-1, :]).any(axis=1)], axis=0)
        self._data = np.around(self._data, decimals=2)

        self.dataChanged.emit(self.index(0, 0), self.index(row, col))

    def export_to_latex(self, filename):
        seqs = [seq.split('_')[0] for seq in self._vertical_headers]
        latex_table = tabulate(self._data, self._horizontal_headers, showindex=seqs, tablefmt="latex_booktabs")

        # create a template class which uses % as the placeholder introducing delimiter, since this is the
        # latex comment character
        class LatexTemplate(Template):
            delimiter = '%'

        # open the template latex file, which has a preamble and add table
        # this produces a file which can already be compiled
        template_file_name = pkg_resources.resource_filename(__name__, 'misc/latex_table_template.tex')
        with open(template_file_name, 'r') as template_file, open(filename, 'w') as output_file:
            latex_template = LatexTemplate(template_file.read())
            new_latex_doc = latex_template.substitute(table_goeth_here=latex_table)
            output_file.write(new_latex_doc)


class BdUserGeneratedCurvesTableModel(BdTableModel):
    def __init__(self):
        super().__init__()

    def data(self, q_index, role):
        if q_index.isValid() and role == Qt.DisplayRole:
            value = self._data[q_index.row(), q_index.column()]
            return QVariant(str(value))
        elif q_index.isValid() and role == Qt.ToolTipRole:
            return 'By double-clicking this item\'s header to the left, you can make it the anchor for the calculation'
        return QVariant()

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self._horizontal_headers)
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return QVariant(self._vertical_headers[col])
        return QVariant()

    def update(self, plot_data_collection, bd_option, interp_option, bd_plot, anchor_text=''):
        # reset the model in the first place and set data afterwards appropriately
        self.beginResetModel()
        self.reset_model()
        self.endResetModel()

        if plot_data_collection is None:
            plot_data_collection = self._plot_data_collection

        # change our anchor to the one that was double-clicked
        # in case of 'AVG' our anchor remains unchanged
        if anchor_text == '':
            self._anchor_index = 0
        else:
            index = 0
            for curve in plot_data_collection:
                if curve.identifiers[0] == anchor_text:
                    self._anchor_index = index
                index += 1

        # there is no need to calculate a bd for just one curve
        if len(plot_data_collection) < 2:
            plt.close()
            return

        elif len(plot_data_collection) > 5 and (not bd_plot):
             msg = QMessageBox()
             msg.setIcon(QMessageBox.Information)
             msg.setText("Your BD plot will contain more than 5 curves, do you really want to continue?")
             msg.setWindowTitle("Info")
             msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
             result = msg.exec()

             if result == QMessageBox.Cancel:
                 plt.close()
                 bd_plot = True

        self._horizontal_headers = plot_data_collection[self._anchor_index].identifiers[0]
        index = 0
        for curve in plot_data_collection:
            if index != self._anchor_index:
                self._vertical_headers.append(curve.identifiers[0])
            index += 1
        self._vertical_headers.append('AVG')

        # insert as many columns as we need for the selected data
        self.beginInsertColumns(QModelIndex(), 0, 0)
        self.insertColumns(0, 1, QModelIndex())
        self.endInsertColumns()

        # insert as many rows as we need for the selected data
        # and add one row for the average
        self.beginInsertRows(QModelIndex(), 0, len(self._vertical_headers) - 1)
        self.insertRows(0, len(self._vertical_headers), QModelIndex())
        self.endInsertRows()

        self._plot_data_collection = plot_data_collection

        self._data = np.zeros((len(self._vertical_headers), 1))
        if all(collection.label == ("kbps", "dB") for collection in plot_data_collection):
            self.update_table(bd_option, interp_option, bd_plot)
        else:
            self.beginResetModel()
            self.reset_model()
            self.endResetModel()
            plt.close()

    def update_table(self, bd_option, interp_option, bd_plot):
        # if there are no rows and columns in the model,
        # nothing can be updated
        if self.rowCount(self) == 0 and self.columnCount(self) == 0:
            return

        anchor_curve = self._plot_data_collection[self._anchor_index]
        c1 = sorted(list(set(anchor_curve.values)))
        index = 0
        table_index = 0
        curve_names = [self._horizontal_headers]
        for curve_name in self._vertical_headers:
            if curve_name != 'AVG':
                curve_names.append(curve_name)
        for curve in self._plot_data_collection:
            if index != self._anchor_index:
                c2 = sorted(list(set(curve.values)))
                self._data[table_index, 0] = bjontegaard(c1, c2, bd_option, interp_option, 'BD Plot', curve_names, bd_plot)
                table_index += 1
            index += 1

        # calculate the AVG rate savings or delta psnr and round the output to something meaningful
        self._data[table_index, 0] = np.mean(np.array(self._data[:-1, 0]), axis=0)
        self._data = np.around(self._data, decimals=2)

        self.dataChanged.emit(self.index(0, 0), self.index(len(self._vertical_headers) - 1, 0))


class AttributesDialog(QDialog):

    message_shown = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.reset = True
        main_layout = QVBoxLayout()
        self.setWindowTitle('Choose Parameters')
        self.setLayout(main_layout)
        msg = QtWidgets.QLabel()
        msg.setText('Additional Parameters have been found.\n'
                    'Move Parameters you want to consider further to the right list.\n')
        main_layout.addWidget(msg)
        list_layout = QHBoxLayout()
        main_layout.addLayout(list_layout)
        # TODO: all items dragged into chosen_par should appear above the qp_item
        self.not_chosen_par = QtWidgets.QListWidget()
        self.chosen_par = QtWidgets.QListWidget()
        self.chosen_par.setDragDropMode(QAbstractItemView.DragDrop)
        self.chosen_par.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.not_chosen_par.setDragDropMode(QAbstractItemView.DragDrop)
        self.not_chosen_par.setDefaultDropAction(QtCore.Qt.MoveAction)
        list_layout.addWidget(self.not_chosen_par)
        list_layout.addWidget(self.chosen_par)
        self.not_chosen_par.show()
        self.chosen_par.show()
        ok_button = QPushButton('OK')
        main_layout.addWidget(ok_button)
        ok_button.clicked.connect(self.close)

    def paintEvent(self, event):
        if self.reset:
            self.message_shown.emit()
            self.reset = False