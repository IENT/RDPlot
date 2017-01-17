import re
from glob import glob
from os.path import (basename, dirname, abspath, join, sep, normpath, isdir,
                     isfile)
from collections import deque
from collections import OrderedDict
from PyQt5.QtCore import QAbstractListModel, QAbstractItemModel, pyqtSignal
from PyQt5.Qt import Qt, QVariant, QModelIndex


def summary_data_from_enc_logs(encLogs):
    """Create a dictionary containing the summary data by combining
       different encLogs."""
    #{'Summary' : {'Y-PSNR' : [...], 'PSNR' : ...}, 'I' : ...}
    output = {}
    for encLog in encLogs:
        seqconf = encLog.sequence + ' ' + encLog.config
        if seqconf not in output:
            output[seqconf] = {}
        for (name1, dict1) in encLog.summary_data.items():
            if name1 not in output[seqconf]:
                output[seqconf][name1] = {}
            for (name2, list2) in dict1.items():
                if name2 not in output[seqconf][name1]:
                    output[seqconf][name1][name2] = []
                output[seqconf][name1][name2].extend(list2)
    return output

def sort_dict_of_lists_by_key(dictionary, sorting_key):
    """Take a dictionary with equal length lists as items and sort all list
       according to one list identified by sorting_key"""
    sorting_list = dictionary[sorting_key]
    sorted_dictionary = {sorting_key : sorted(sorting_list)}
    for (key, item) in dictionary.items():
        if key != sorting_key:
            sorted_pairs = sorted(zip(sorting_list, item),
                                  key=lambda zipped: zipped[0])
            sorted_dictionary[key] = list(zip(*sorted_pairs))[1]
    return sorted_dictionary


class EncLogParserError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class EncLog():
    def __init__(self, path):
        #Path is unique identifier
        self.path = abspath(path)

        #Parse file path and set additional identifiers
        self.sequence, self.config, self.qp = self._parse_path(self.path)

        #Dictionaries holding the parsed values
        #TODO select parsing functions depending on codec type,
        self.summary_data  = self._parse_summary_data(self.path)
        self.temporal_data = {self.qp : self._parse_temporal_data(self.path)}

    @classmethod
    def parse_url(cls, url):
        """Parse a url and return either all encoder logs in the folder, all
           logs in a subfolder log or all encoder logs with the same sequence as
           the file."""
        # Parse url as directory. Check for encoder log files in directory and
        # in a possible 'log' subdirectory
        if isdir(url) == True:
            enc_logs = list( cls.parse_directory(url) )
            if len(enc_logs) != 0:
                return enc_logs

            url_log = join(url, 'log')
            if isdir( url_log ) == True:
                enc_logs = list( cls.parse_directory(url_log) )
                if len(enc_logs) != 0:
                    return enc_logs

        # Parse url as encoder log path. Search in same directory for encoder
        # logs with same sequence
        if isfile(url) == True:
            enc_logs = list( cls.parse_directory_for_sequence(url) )
            if len(enc_logs) != 0:
                return enc_logs

        # No parsing scheme succeeded
        raise EncLogParserError( "Could not parse url {} for encoder logs"
                                .format(url) )

    @classmethod
    def parse_directory(cls, directory_path):
        """Parse a directory for all encoder log files and return generator
           yielding :class: `EncLog`s"""
        #TODO join vs sep and glob pattern?
        paths = glob(join(directory_path, '*_enc.log'))

        return (EncLog(p) for p in paths)

    @classmethod
    def parse_directory_for_sequence(cls, sequence_file_path):
        """Parse a directory for encoder logs of a specific sequence given one
           encoder log of this sequence returning a generator yielding parsed
           encoder :class: `EncLog`s"""
        filename = basename(sequence_file_path)
        directory = dirname(sequence_file_path)
        sequence = filename.rsplit('_QP', 1)[0]

        #Search for other encoder logs in directory and parse them
        #TODO hardcoded file ending, needed to prevent ambiguous occurence
        #exceptions due to *.csv or other files being parsed
        paths = glob(directory + sep + sequence + '*_enc.log')

        return (EncLog(p) for p in paths)

    @staticmethod
    def _parse_path(path):
        try:
            # Assumes structure of .../<simulation_directory>/log/<basename>
            directories = normpath(path).split(sep)[0 : -2]
            filename    = basename(path)
        except IndexError:
            raise EncLogParserError(
                "Path {} can not be splitted into directories and filename"
                .format(filename, path)
            )

        try:
            seperator = '-'
            filename_splitted = filename.split('_QP')[0].split(seperator)
            sequence = filename_splitted[-1]
            config = seperator.join(filename_splitted[0 : -2])
        except IndexError:
            raise EncLogParserError((
                "Filename {} can not be splitted into config until '{}' and"
                " sequence between last '{}' and '_QP'"
            ).format(filename, seperator, seperator))

        # prepend simulation directory to config
        config = directories[-1] + ' ' + config

        m = re.search(r'_QP(\d*)_', filename)
        if m:
            qp = m.group(1)
        else:
            raise EncLogParserError(
                "Basename {} of path {} does not contain a valid qp value"
                .format(filename, path)
            )
        return (sequence, config, qp)

    @staticmethod
    def _parse_temporal_data(path):
        #this function extracts temporal values
        with open(path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            tempData = re.findall(r"""
                POC \s+ (\d+) \s+ .+ \s+ \d+ \s+ . \s+ (.-\D+) ,  #Slice
                \s .+ \) \s+ (\d+) \s+ (.+) \s+ \[ (\D+) \s+ (\d+.\d+) \s+ #Y PSNR
                \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ # U PSNR
                \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ # v PSNR
                """, log_text, re.M + re.X)

            #Association between index of data in tempData and corresponding
            #output key. Output shape definition is in one place.
            names = {0 : 'Frames', 2 : 'Bits', 5 : 'Y-PSNR', 7 : 'U-PSNR',
                     9 : 'V-PSNR'}

            #Define output data dict and fill it with parsed values
            data = {name : [] for (index, name) in names.items()}
            for i in range(0, len(tempData)):
                #TODO slices and frames?
                for (index, name) in names.items():
                    data[name].append(tempData[i][index])
            return data

    @staticmethod
    def _parse_summary_data(path):
        with open(path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            summaries = re.findall(r"""  ^(\w*)-*.*$ # catch summary line
                           \s* # catch newline and space
                           (.*)\| # catch phrase Total Frames / I / P / B
                           (\s*\S*)(\s*\S*)(\s*\S*)(\s*\S*)(\s*\S*)# catch rest of the line
                           \s* # catch newline and space
                           (\d*\s*)\w # catch frame number
                           (\s*\d*\.\d*)(\s*\d*\.\d*)(\s*\d*\.\d*)(\s*\d*\.\d*)(\s*\d*\.\d*) # catch the fractional number (rate, PSNRs)
                      """, log_text, re.M + re.X)

            data = {}
            for summary in summaries:
                summary_type = summary[0]
                # Create upon first access
                if summary_type not in data:
                    data[summary_type] = {}
                names = summary[1:7]
                vals = summary[7:]

                names = [name.strip() for name in names]  # remove leading and trailing space
                vals = [float(val) for val in vals]  # convert to numbers

                name_val_dict = dict(zip(names, vals))  # pack both together in a dict
                # print(summary_type)

                # now pack everything together
                for name in names:
                    if name not in data[summary_type]: # create upon first access
                        data[summary_type][name] = []
                    data[summary_type][name].append(name_val_dict[name])
            return data

    @property
    def tree_path(self):
        return [self.sequence, self.config, self.qp]

    def __eq__(self, enc_log):
        return self.path == enc_log.path

    # TODO remove if usefull 'set' is implemented
    def __hash__(self):
        return hash(self.path)

    def __str__(self):
        return str((
            "Encoder Log of sequence '{}' from config '{}' with qp '{}'"
            " at path {}"
       ).format(self.sequence, self.config, self.qp, self.path))

    def __repr__(self):
        return str(self)

#-------------------------------------------------------------------------------


#
# Models
#


class ModelError(Exception):
    """Error class for model"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AmbiguousEncoderLogs(ModelError):
    """Error class for ambiguous encoder logs"""
    pass



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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dict = OrderedDict()


    # Qt interface methods

    def rowCount(self, parent):
        return len(self._dict)

    def data(self, qIndex, role):
        if qIndex.isValid() and role == Qt.DisplayRole:
            for index, (key, item) in enumerate(self._dict.items()):
                if index == qIndex.row():
                    return QVariant( key )
        return QVariant()


    # Reimplement dictionary methods.
    # Note, that implementation of __setitem__ and pop is done using
    # custom methods, so that *items_changed* is emitted correctly.

    def __getitem__(self, key):
        return self._dict[key]

    def __setitem__(self, key, item):
        self.update( (key, item) )

    def pop(self, key):
        item = self[key]
        self.remove_keys( [key] )
        return items

    def __iter__(self):
        return iter( self._dict )

    def __contains__(self, key):
        return key in self._dict

    def __len__(self):
        return len( self._dict )

    def __str__(self):
        return str( list( self._dict ) )

    def __repr__(self):
        return str( self )

    def values(self):
        return self._dict.values()


    # Implement specific methods
    # Note, that these methods allow update of whole ranges of data and emit
    # the *items_changed* signal afterwards. This allows more efficient update
    # behavior.

    def update_from_tuples(self, tuples):
        """Add/replace items to the dictionary specified in the iterable :param:
        *tuples* of (key, item) pairs. Emit *items_changed* afterwards.
        """

        for key, item in tuples:
            # Iterate to find index corresponding to key in ordered dict
            length = len(self._dict)
            for index, oldkey in enumerate(self._dict):
                if oldkey == key:
                    length = index

            # Call Qt interface functions and add/replace item corresponding
            # to key
            self.beginInsertRows(QModelIndex(), length, length + 1)
            self._dict[key] = item
            self.endInsertRows()

        self.items_changed.emit()

    def clear_and_update_from_tuples(self, tuples):
        """Clear the dictionary and update it the (key, item) pairs specified
        in *tuples*. Emit *items_changed* afterwards.

        :param tuples: Iterable of tuples of (key, item) which are added
            to the dictionary."""

        # Call Qt interface functions and remove all keys and corresponding
        # items from the dictionary
        self.beginRemoveRows(QModelIndex(), 0, len( self ) - 1)
        self._dict.clear()
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
            for index, key_other in enumerate(self._dict):
                if key_other == key:
                    break

            # Call Qt interface functions and remove key and corresponding item
            self.beginRemoveRows(QModelIndex(), index, index + 1)
            self._dict.pop(key)
            self.endRemoveRows()

        self.items_changed.emit()


# Tree model OrderedDictTreeModel is subclass of QAbstractItemModel class,
# and implements the abstract methods, thus, the model valid for Qt QTreeView.
# The OrderedDictTreeItem class implements items of the tree model.
# Implementation was done according to the example at
# http://doc.qt.io/qt-5/qtwidgets-itemviews-simpletreemodel-example.html
# and corresponding files under BSD licence.

class OrderedDictTreeItem():
    """Item of :class: `OrderedDictTreeModel`. The item imitates the
    behavior of a dictionary, thus, the children of an item can be accessed
    using slice notation and their identifiers, eg.:

    >>> parent['child_identifier']

    In contrast to that, slice assignement is **not** supported. This
    would not be very usefull, as the key to an item is **always** its
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
    :param children: Iterable of childrens of the item
    :param values: Values contained by the item
    """

    def __init__(self, identifier=None,  parent=None, children=None,
                 values=None):
        self._identifier = identifier
        self._parent     = parent

        self._children  = []
        if children is not None:
            self.extend(children)

        self.values = set() if values is None else values


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
        return list( self._children )


    # Special functions/properties

    @property
    def leafs(self):
        """Walk all items below the item in the tree and return all leafs ie.
        items which do not have any children themselves.

        :rtype: `list` of :class: `OrderedDictTreeItem`s
        """

        items = deque( [self] )

        leafs = deque()
        while len( items ) != 0:
            item = items.pop()

            items.extend( item.children )
            if len( item ) == 0:
                leafs.append( item )

        return list( leafs )

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
        return {identifier : self[identifier].dict_tree for identifier in self}

    @property
    def path(self):
        """Walk up the path up until the root item and return list of all passed
        items.

        :rtype: :class: `list` of :class: `OrderedDictTreeItem`
        """

        path = deque( [self] )
        item = self
        while item.parent is not None:
            path.appendleft(item.parent)
            item = item.parent

        return list( path )


    # Functions to add/remove children of the item

    def _add(self, child):
        child._parent = self

        # If a child with the identifier is already present it is replaced, else
        # the child is inserted at the end
        if child in self:
            index = self._children.index(child.identifier)
            self._children[index] = child
        else:
            self._children.append( child )

    def _update(self, children):
        for child in children:
            self.add(child)

    def _remove(self, child):
        child._parent = None
        self._children.remove(child)


    # Reimplement some dictionary functions

    def __getitem__(self, identifier):
        """Get child by *identifier*"""

        for child in self._children:
            if child.identifier == identifier:
                return child

        raise KeyError("Key {key} not found in item {item}".format(
            key     = identifier,
            item    = str(self)
        ))

    def __len__(self):
        """Number of children"""
        return len( self._children )

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
        return str( self.identifier )

    def __repr__(self):
        """Display item as dictionary tree"""
        return str( self.dict_tree )


class OrderedDictTreeModel(QAbstractItemModel):
    def __init__(self, *args, default_item_values=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Default item values
        if default_item_values is None:
            default_item_values = set()
        self._default_item_values = default_item_values

        self._root = OrderedDictTreeItem(values=self._default_item_values)


    # Properties

    @property
    def root(self):
        return self._root


    # Qt interface functions implemented according to
    # http://doc.qt.io/qt-5/qtwidgets-itemviews-simpletreemodel-example.html

    def index(self, row, column, q_parent_index):
        if self.hasIndex(row, column, q_parent_index) == False:
            return QModelIndex()
        if q_parent_index.isValid() == True:
            item = q_parent_index.internalPointer().children[ row ]
            return self.createIndex(row, 0, item)
        return self.createIndex(row, column, self.root.children[row])

    def parent(self, q_parent_index):
        if q_parent_index.isValid() == True:
            parent = q_parent_index.internalPointer().parent
            if parent != self.root:
                row = parent.parent.children.index(parent)
                return self.createIndex(row, 0, parent)
        return QModelIndex()

    def rowCount(self, q_parent_index):
        # TODO Handle different column values
        if q_parent_index.isValid() == True:
            return len( q_parent_index.internalPointer() )
        return len(self.root)

    def columnCount(self, q_parent_index):
        # All items only hold their own identifier as data to be displayed,
        # thus, the agument is irrelevant
        return 1

    def data(self, q_parent_index, q_role):
        if q_parent_index.isValid() == True and q_role == Qt.DisplayRole:
            return QVariant( str( q_parent_index.internalPointer() ) )
        return QVariant()


    # Non-Qt interface functions

    def create_path(self, *path):
        """Create all items along *path* if they are not already present. Return
        last *item* of the path.

        :param *path: Accepts an arbitrary number of *identifiers* as path

        :rtype: :class: `OrderedDictTreeItem`

        """

        # Each path starts at root item *item_parent* and root *q_index_parent*
        item_parent = self.root
        q_index_parent = QModelIndex()

        # Walk the path
        for index, key in enumerate(path):
            # If *key* is not already present as child on *item_parent*, add it
            if key not in item_parent:
                # Always add as last child
                row = len(item_parent)
                # Call Qt update functions
                self.beginInsertRows(q_index_parent, row, row)
                item = OrderedDictTreeItem(
                    identifier  = key,
                    values      = self._default_item_values.copy(),
                )
                item_parent._add( item )
                self.endInsertRows()

            # Set the current item as *item_parent* for next iteration, and
            # update the *q_index_parent* accordingly
            item_parent = item_parent[key]
            row = self._get_row_from_item_and_index_parent(item_parent, q_index_parent)
            q_index_parent = self.index(row, 0, q_index_parent)

        # Note, that *item_parent* is now the last item specified by path
        return item_parent

    def _get_index_parent_from_item(self, item):
        """Get the :class: `QModelIndex` *q_parent_index* of the parent item of
        *item*. Note, that the tree has to walked up and down again
        to find the index, so performance depens on the depth of the tree.

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

    def _get_row_from_item_and_index_parent(self, item, q_index_parent):
        """Get the row of an *item* in reference to its parent at
        *q_parent_index*.

        :param item: Get the position of :class: `OrderedDictTreeItem`
        :param q_index_parent: :class: `QModelIndex` of the parent of *item*

        :rtype: :class: `Int`
        """

        if q_index_parent.isValid() == True:
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
            q_index_parent = self._get_index_parent_from_item( item )

        # Get the row position of the *item* relative to its parent
        row = self._get_row_from_item_and_index_parent(item, q_index_parent)

        # Before removing *item* itself, recursively remove all sub items, if
        # there are any
        if len( item ) > 0:
            q_index = self.index(row, 0, q_index_parent)
            for child in item:
                self.remove_item(item[child], q_index)

        parent = item.parent

        # Remove *item* itself and notify view
        self.beginRemoveRows(q_index_parent, row, row)
        parent._remove(item)
        self.endRemoveRows()

        # Remove parent item recursively if
        # * the parent item has no children
        # * the parent item does not contain any values
        # * the parent item is not the root item
        condition = (
                len( parent )        == 0
            and len( parent.values ) == 0
            and parent.parent is not None
        )
        if condition:
            self.remove_item(parent, self.parent( q_index_parent ))

    def clear(self):
        """Remove all items except the *root* item from the tree."""

        for child in self.root:
            self.remove_item(self.root[child], QModelIndex())

    def __repr__(self):
        return str( self.root.dict_tree )


class EncoderLogTreeModel(OrderedDictTreeModel):
    """Tree model specific to encoder logs, specifying methods to add them to
    the tree, how to store their data at the tree and how to access them, using
    the tree. Implements *item_changed* signal, which is emitted after the
    tree model has been altered. With :func: `add`, :func: `update` and :func:
    `emove`, the signal allows altering a collection of items and efficiently
    updating the GUI, as *item_changed* is emitted, after all model alterations
    have been processed.

    :param is_summary_enabled: :class: `Bool` Define if the tree should render
        for summary or temporal data.
    :param *args:    Pass to superclass
    :param **kwargs: Pass to superclass
    """

    items_changed = pyqtSignal()

    def __init__(self, *args, is_summary_enabled=True, **kwargs):
        super().__init__(*args, **kwargs)

        self._is_summary_enabled = True
        self.is_summary_enabled = is_summary_enabled

    # Properties

    @property
    def is_summary_enabled(self):
        return self._is_summary_enabled

    @is_summary_enabled.setter
    def is_summary_enabled(self, enabled):
        # TODO Write doc
        if enabled != self._is_summary_enabled:
            self._is_summary_enabled = enabled

            if self._is_summary_enabled:
                for leaf in self.root.leafs:
                    leaf.parent.values.update( leaf.values )
                    self.remove_item(leaf)
            else:
                for leaf in self.root.leafs:
                    for value in leaf.values:
                        item = self.create_path(
                            value.sequence, value.config, value.qp
                        )
                        item.values.add(value)
                    leaf.values.clear()

            self.items_changed.emit()


    # Implement *add*, *update* and remove to add/remove encoder logs to the
    # tree.
    # Note, that *add* is implemented using update, so *items_changed* is
    # emitted efficiently.

    def add(self, enc_log):
        """Like update, but for a single *enc_log*. *items_changed* is issued
        by calling :func: `update` .

        :param enc_log: :class: `EncLog` to be added to tree
        """
        self.update([enc_log])

    def update(self, enc_logs):
        """Adds all elements in the iterable *enc_logs* to the tree or
        replaces them if they are already present. Issues the *items_changed*
        signal, after all encoder logs are added/replaced.

        :param enc_logs: Iterable collection of :class: `EncLog`s to be added
        """

        for enc_log in enc_logs:
            # Get *item* of the tree corresponding to *enc_log*
            if self.is_summary_enabled:
                item = self.create_path(
                    enc_log.sequence,
                    enc_log.config
                )
            else:
                item = self.create_path(
                    enc_log.sequence,
                    enc_log.config,
                    enc_log.qp
                )

            # TODO Tree access is not unique in
            # filesystem. This prevents an encoder log overwriting another one
            # with same sequence, config and qp but on a different location. The
            # question is, if this should be the case?
            for value in  item.values:
                # Condition of ambiguous occurence is that identifiers are
                # similar, but the paths are different
                condition = (
                        value.sequence  == enc_log.sequence
                    and value.config    == enc_log.config
                    and value.qp        == enc_log.qp
                    and value.path      != enc_log.path
                )
                if condition:
                    raise AmbiguousEncoderLogs((
                        "Ambigious encoder logs: Encoder log at {} and {} have"
                        " the same sequence '{}', dir '{}' and qp '{}', but"
                        " different absolute paths."
                    ).format(value.path, enc_log.path, enc_log.sequence,
                             enc_log.config, enc_log.qp))

            # Add *enc_log* to the set of values of the tree item *item*
            item.values.add( enc_log )

        self.items_changed.emit()

    def remove(self, enc_logs):
        """Remove all elements in iterable collection *enc_logs* from the tree.
        Emit *items_changed* signal after all encoder logs are removed.

        :param enc_logs: Iterable collection of :class: `EncLog`s to be removed
        """

        for enc_log in enc_logs:
            # Get *item* of the tree corresponding to *enc_log*
            if self.is_summary_enabled == True:
                item = self.create_path(
                    enc_log.sequence,
                    enc_log.config
                )
            else:
                item = self.create_path(
                    enc_log.sequence,
                    enc_log.config,
                    enc_log.qp
                )

            self.remove_item(item)

        self.items_changed.emit()
