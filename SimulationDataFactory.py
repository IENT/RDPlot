from os.path import (basename, dirname, join, sep)
from glob import glob
import re



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
