import pkgutil
import re

from abc import ABCMeta, abstractmethod, abstractproperty
from os.path import basename, dirname, join, abspath, isfile, isdir
from os import listdir
from collections import deque



#
# Classes
#

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

        # TODO Stackoverflow refs

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
        for cls in self._classes:
            if cls.can_parse_file( file_path ):
                return cls( file_path )

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
                item_list.append( self.create_item_from_file( path ) )
            except SimulationDataItemError as error:
                print((
                    "Could not create simulation data item from file '{}'"
                    " due to {}"
                ).format(path, error))

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
