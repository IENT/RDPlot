import pkgutil
import re

from abc import ABCMeta, abstractmethod, abstractproperty
from os.path import basename, dirname, join, abspath, isfile, isdir
from os import listdir
from collections import deque
from copy import copy


#
# Functions
#


def is_class(cls):
    """Check if *cls* is a class by trying to access its *__bases__* attribute
    """
    return hasattr(cls, '__bases__')


def dict_tree_from_sim_data_items(sim_data_item_collection):
    """Combine the *data* of different sim data items to a tree of
    :class: `dicts`, which is then used to display the data. To understand, why
    this is necessary, and what this method does, take a look at the
    documentation of the :class: `SimulationDataItem` *data* property.

    :param sim_data_item_collection: Iterable of :class: `SimDataItem`s

    :rtype: tree of :class: `dict`s with :class: `list`s of
        :class: `PlotData` objects as leafs
    """

    dict_tree = {}

    for sim_data_item in sim_data_item_collection:
        for (identifiers, sim_data_item_dict_tree) in sim_data_item.data:

            # Process all items of the *encoder_log*'s dictionary tree ie.
            # create corresponding keys in the output *dict_tree* and
            # copy the data at the corresponding position in PlotData
            # objects.

            # Note, that tuple in queue are pairs of path ie. a list of
            # strings/keys of the encoder_log_dict_tree, and the tree itself.
            # deque has to be initialized with iterable, thus, pair is wrapped
            # with list.
            tree_queue = deque([([], sim_data_item_dict_tree)])

            while len(tree_queue) > 0:
                (keys, parent) = tree_queue.pop()

                # Dictionary items are added to the queue to be processed
                # themselves
                if isinstance(parent, dict):
                    for key, item in parent.items():
                        tree_queue.appendleft((keys + [key], item))
                    continue

                # Non dictionary items are processed ie. their data is
                # added as PlotData object to the output *dict_tree*
                dict_tree = append_value_to_dict_tree_at_path(
                    dict_tree,
                    keys,
                    PlotData(identifiers, copy(parent), keys),
                )

    return dict_tree


def append_value_to_dict_tree_at_path(dict_tree, path, plot_data):
    """Add a *plot_data* object to a *dict_tree* at a certain *path*.

    :param dict_tree: Tree of nested :class: `dict`s
    :param path: :class: `list` of keys describing a path in the *dict_tree*
    :param plot_data: :class: `PlotData` object to be added to the *dict_tree*

    :rtype: Altered tree of nested :class: `dict`s
    """

    # Walk the *path* down at the *dict_tree* and create not existing keys
    # on the way.
    # Note, that the last key of the path is excluded, as the data has
    # to be written to this key.
    item = dict_tree
    for key in path[:-1]:
        # Create nested dictionaries if they do not exist already
        if key not in item:
            item[key] = {}

        item = item[key]

    # If the last element of the path does not exist, create a list on the
    # corresponding position in the *dict_tree* with the *plot_data* object
    # as only member so far. Return.
    if path[-1] not in item:
        item[path[-1]] = [plot_data]
        return dict_tree

    # If the last element does exist, retrieve the list stored at its position
    plot_data_list = item[path[-1]]

    # Iterate over the existing PlotData objects and check, if one has equal
    # identifiers to the current one. If this is the case, append the values
    # stored in the current *plot_data* object to one already present. Return.
    for plot_data_other in plot_data_list:
        if plot_data_other.identifiers == plot_data.identifiers:
            plot_data_other.values.extend(plot_data.values)
            return dict_tree

    # If the last element exists, but no PlotData object with the same
    # identifiers is present, append the PlotData object *plot_data* to the
    # list.
    plot_data_list.append(plot_data)
    return dict_tree

#-------------------------------------------------------------------------------



#
# Classes
#

# TODO replace this by named tuple
# TODO remove path and implement functionality in main

class PlotData:
    """Class encapsulating data to be plotted. It is used to join data from
    different simulation data items together, if they export data
    at the same position in the variable tree, and with the same *identifiers* .

    :param identifiers: Used to decide, if a list of values should be
        associated with a certain plot data object.
    :type identifiers: :class: `list`

    :param values: The actual data ie. a list of x, y pairs
    :type values: :class: `list` of :class: `tuples` of double/int/...

    :param path: Path of the plot data object in the variable tree
    :type path: :class: `list` of :class: `str`
    """

    def __init__(self, identifiers, values, path):
        self.identifiers    = identifiers
        self.values         = values
        self.path           = path


class SimulationDataItemError(Exception):
    pass

class IsNotAnAbstractSimulationDataItemSubClassError(SimulationDataItemError):
    pass



class AbstractSimulationDataItem(metaclass=ABCMeta):
    """Abstract base class for simulation data item classes. The abstract
    method :func: `can_parse_file` and the properties *data*, and
    *tree_identifier_list* have to be implemented by sub classes.

    :param path: Path of associated file in file systems. Is used as unique
        identifier.
    :type path: :class: `str`
    """

    # Constructor

    def __init__(self, path):
        # Path is unique identifier
        self.path = abspath(path)


    # Abstract Methods/Properties

    @classmethod
    @abstractmethod
    def can_parse_file(cls, path):
        """Check, if the file at *path* can be parsed by the class. The class
        can can for example check, if the file name or the file extension
        matches a certain pattern, or inspect the contents of the file. Note,
        that the first class which returns ``True`` with respect to a file on
        this method, will be be used to parse the file. Thus, classes should
        implement this method as specific as possible.

        :param path:  path to file
        :type path: :class: `String`

        :rtype: :class: `Bool`
        """
        pass

    @abstractproperty
    def data(self):
        """Property to access the parsed data. The data is given as a list of
        pairs. The first element are the identifiers associated with the data,
        eg. *sequence* and  *config* for summary data. The second element is the
        data itself, in the form of a dictionary tree. The  dictionary tree
        has the variables which are provided by the *encoder_log* as keys, and
        the actual data as leafs. The data  is in the form of lists of 2-tuples
        containing, an x and the  corresponding y value.


        Now, the dictionary trees of different sim data items have to be
        combined to one dictionary tree. The resulting *dict_tree* is the union
        of the trees of the sim data items with :class: `list`s of
        :class: `PlotData` objects as leafs.

        The leafs are created as follows: A :class: `PlotData` object is
        created from the *identifiers* associated with the :class: `SimDataItem`
        and the list of value pairs found at the current position. The current
        path in the dictionary tree is also added for convenience. Now, if there
        are already :class: `PlotData` objects present at the current leaf of
        the *dict_tree*, then:
            * if the identifiers of the current :class: `PlotData` object equal
                the one of an already present one, the values are just added
                to the values of the :class: `PlotData` object already present.
            * if no :class: `PlotData` object is present with equal identifiers
                the new :class: `PlotData` object is added to the list

        Why is this necessary? It might be, that different sim data items
        provide data, that has to be joined before it is displayed, eg. the
        summary data for one particular variable is usually provided by several
        encoder_logs. In this case, the correspondence of the data is coded
        in the identifier of the data ie. the identifier would be similar across
        different sim data items, and thus, the data can be joined by this
        function. On the other hand, if several sim data items just provide data
        for the same variable, then the data should be rendered separately, ie.
        different :class: `PlotData` objects are added to the list for each
        :class: `SimDataItem` object.

        :rtype: :class: `list` of :class: `tuple`s with a :class: `list` of
            :class: `str` identifiers as first, and a nested :"""
        pass

    @abstractproperty
    def tree_identifier_list(self):
        """Property to acces a list of identifiers, used to specify the position
        of simulation data items in the tree view.

        :rtype: :class: `list` of :class: `str`
        """
        pass


    # Magic Methods

    # TODO remove if usefull 'set' is implemented
    def __hash__(self):
        return hash(self.path)

    def __str__(self):
        return str( "SimulationDataItem at path {}".format(self.path) )

    def __repr__(self):
        return str(self)


    # Helper Methods

    @classmethod
    def _is_file_text_matching_re_pattern(cls, path, pattern):
        """Check, if the file at *path* matches the given regex *pattern*
        """
        with open(path, 'r') as simulation_data_item_file:
            text = simulation_data_item_file.read()
            return bool( re.search(pattern, text, re.M + re.X) )
        raise SimulationDataItemError( "Could not open file {}".format(path) )



class SimulationDataItemFactory:
    """This class is a factory for all sub classes of the :class:
    `AbstractSimulationDataItem` class.

    Sub classes can be passed, to the constructor or added by the
    :func: `add_class` method. Additionally, a class method constructor
    :func: `from_path` creates a factory instance from all sub classes found in
    all python files in a directory.

    Multiple methods are provided to create simulation data items and
    collections of simulation data items from paths using the sub classes known
    to the factory. The factory determines, if it can create a simulation data
    item using a class, by checking the class method *can_parse_file* of this
    class. Note, that the order of the classes is therefore important, as the
    first matching class will be used to create the item. Thus, more general
    items should be tried at last.
    """

    # Constructors

    def __init__(self, classes=None):
        self._classes = set()

        if classes is not None:
            for cls in classes:
                self.add_class( cls )

    @classmethod
    def from_path(cls, directory_path):
        """Create a *SimulationDataItemFactory* by parsing a directory at
        *directory_path* for sub classes of *AbstractSimulationDataItem*. All
        python modules in the directory are parsed, and all sub classes are
        passed to the factory. Packages are NOT parsed.

        :param directory_path String: Path to parse for
            *AbstractSimulationDataItem* sub classes

        :rtype: :class: `SimulationDataItemFactory` with sub classes of
            :class: `AbstractSimulationDataItem` from *directory_path*
        """

        simulationDataItemFactory = cls()

        # Automated loading of python modules from a directory adapted from
        # Luca Invernizzi's answer to
        # http://stackoverflow.com/questions/1057431/loading-all-modules-in-a-folder-in-python

        # Parse *directory_path* for sub classes of *AbstractSimulationDataItem*
        classes = []
        for importer, name, _ in pkgutil.iter_modules( [directory_path] ):
            # Import a module from *directory_path*
            module = importer.find_module( name ).load_module( name )

            # Add all sub classes of AbstractSimulationDataItem from the module
            # to the factory
            for _, module_item in module.__dict__.items():
                if is_class( module_item ):
                    try:
                        simulationDataItemFactory.add_class( module_item )
                        # TODO usefull logging
                        print((
                            "Added sub class '{}' to simualtion data item "
                            " factory"
                        ).format(module_item))
                    except IsNotAnAbstractSimulationDataItemSubClassError:
                        pass

        return simulationDataItemFactory


    # Interface to Set of Classes

    def add_class(self, cls):
        """Add a sub class *cls* of :class: `AbstractSimulationDataItem` to the
        factory.
        """
        if not issubclass(cls, AbstractSimulationDataItem):
            raise IsNotAnAbstractSimulationDataItemSubClassError((
                "Can not add class '{}' to SimulationDataItemFactory, as it is "
                "not a sub class of AbstractSimulationDataItem"
            ).format(cls))

        self._classes.add( cls )


    # Factory Methods

    def create_item_from_file(self, file_path):
        """Create an item of a AbstractSimulationDataItem sub class for the
        file specified by *file_path*.

        :param file_path: File which should be parsed as simulation data
            item_generator

        :rtype: object of sub class of :class: `AbstractSimulationDataItem`
        """

        # Create simulatin data item of the first class which says, it can parse
        # the file
        cls_list = []
        for cls in self._classes:
            if cls.can_parse_file( file_path ):
                cls_list.append( cls( file_path ))
        return cls_list

        raise SimulationDataItemError((
            "Could not create a simulation data item from file at '{}' using"
            " the sub classes of *AbstractSimulationDataItem* known to the"
            " SimulationDataItemFactory."
        ).format(file_path))

    def create_item_list_from_directory(self, directory_path):
        """Try to create simulation data items for all files in a directory at
        *directory_path*. Ignore if files can not be parsed.

        :param directory_path: :class: `str` of directory path

        :rtype: :class: `list` of simulation data items
        """

        item_list = []
        for file_name in listdir(directory_path):
            path = join(directory_path, file_name)
            try:
                item_list.extend( self.create_item_from_file( path ) )
            except SimulationDataItemError as error:
                pass
                # We definitely cannot accept thousands of execptions on the command line
                #print((AbstractEncLog
                #    "Could not create simulation data item from file '{}'"
                #    " due to {}"
                #).format(path, error))

        return item_list

    def create_item_list_from_path(self, path):
        """Create a list of simulation data items from a path. The path can
        either be a file or a directory and is parsed accordingly. The
        method fails if not at least one simulation data item can be
        created.

        :param path: :class: `str` path

        :rtype: :class: `list` of simulation data items
        """

        if isfile(path):
            return [ self.create_item_from_file( path ) ]
        if isdir(path):
            item_list = self.create_item_list_from_directory( path )
            if len( item_list ) == 0:
                raise SimulationDataItemError()
            return item_list

        raise SimulationDataItemError((
            "Not at least one simulation data item can be created from path"
            " '{}'"
        ).format(path))


    # Magic Methods

    def __str__(self):
        return str( self._classes )

    def __repr__(self):
        return str(
            "SimulationDataItemFactory with loaded classes: "
            .format( str(self) )
        )
