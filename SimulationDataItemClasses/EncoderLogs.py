class SimDataItemParserError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class SimDataItem:
    def __init__(self, path):
        # Path is unique identifier
        self.path = abspath(path)

        # Parse file path and set additional identifiers
        # self.logType = self._get_Type(path)
        self.sequence, self.config, self.qp = self._parse_path(self.path)

        # Dictionaries holding the parsed values
        self.summary_data = self._parse_summary_data()
        self.temporal_data = self._parse_temporal_data()

    # Properties
    @property
    def tree_path(self):
        return [self.sequence, self.config, self.qp]

    @property
    def data(self):
        return [
            ([self.sequence, self.config, self.qp], {'Temporal': self.temporal_data}),
            ([self.sequence, self.config], {'Summary': self.summary_data}),
        ]

    # Magic methods
    def legend(self):
        return " ".join(self.sequence, self.config, self.qp)

    def __eq__(self, sim_data_item):
        return self.path == sim_data_item.path

    # TODO remove if usefull 'set' is implemented
    def __hash__(self):
        return hash(self.path)

    def __str__(self):
        return str((
                       "Sim Data Item of sequence '{}' from config '{}' with qp '{}'"
                       " at path {}"
                   ).format(self.sequence, self.config, self.qp, self.path))

    def __repr__(self):
        return str(self)

    # Conctructors
    @classmethod
    def parse_url(cls, url):
        """Parse a url and return either all sim data items in the folder, all
           logs in a subfolder log or all sim data items with the same sequence as
           the file."""
        # Parse url as directory. Check for encoder log files in directory and
        # in a possible 'log' subdirectory
        if isdir(url):
            sim_data_items = list(cls.parse_directory(url))
            if len(sim_data_items) != 0:
                return sim_data_items

            url_log = join(url, 'log')
            if isdir(url_log):
                sim_data_items = list(cls.parse_directory(url_log))
                if len(sim_data_items) != 0:
                    return sim_data_items

        # Parse url as encoder log path. Search in same directory for encoder
        # logs with same sequence
        if isfile(url):
            sim_data_items = list(cls.parse_directory_for_sequence(url))
            if len(sim_data_items) != 0:
                return sim_data_items

        # No parsing scheme succeeded
        raise SimDataItemParserError("Could not parse url {} for sim data items"
                                     .format(url))

