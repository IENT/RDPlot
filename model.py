import re

import glob
from os.path import basename, dirname, abspath, join, sep, normpath
from glob import glob

from model_view import Model


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
    def parse_directory(cls, directory_path):
        """Parse a directory for all encoder log files in subfolder "log" and
           return generator yielding :class: `EncLog`s"""
        #TODO join vs sep and glob pattern?
        paths = glob(join(directory_path, 'log') + sep + '*_enc.log')

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

    def __eq__(self, enc_log):
        return self.path == enc_log.path

    def __str__(self):
        return str((
            "Encoder Log of sequence '{}' from config '{}' with qp '{}'"
            " at path {}"
       ).format(self.sequence, self.config, self.qp, self.path))

    def __repr__(self):
        return str(self)

class EncLogCollectionModel(Model):
    _max_tree_depth = 3

    """Collection of :class: `model.EncLog`s. The class implements different
       access/iteration/etc. methods. Additionally it implements parsing the
       file system for certain encoder logs eg. all encoder logs of one sequence
       in different folders."""
    def __init__(self, views=None, enc_logs=None):
        super().__init__(views)
        #References to the encoder logs are stored in a flat dictionary using
        #the path/unique identifier as key and a tree using sequence, config and
        #qp as key
        self._flat = {}
        self._tree = {}
        if enc_logs is not None:
            self.update(enc_logs)

    def add(self, enc_log):
        """Adds :param: `enc_log` to the collection or replaces it if it is
           already in the collection."""
        #Eventually the tree has to be extended if new sequences are added ie.
        #additionaly dictionaries have to be inserted before the encoder log can
        #be appended
        if enc_log.sequence not in self._tree:
            self._tree[enc_log.sequence] = {}
        if enc_log.config not in self._tree[enc_log.sequence]:
            self._tree[enc_log.sequence][enc_log.config] = {}

        #TODO Tree access is not unique in
        #filesystem. This prevents an encoder log overwriting another one with
        #same sequence, config and qp but on a different location. The question
        #is, if this should be the case?
        if enc_log.qp in self._tree[enc_log.sequence][enc_log.config]:
            old_enc_log = self._tree[enc_log.sequence][enc_log.config][enc_log.qp]
            if old_enc_log != enc_log:
                raise Exception((
                    "Ambigious encoder logs: Encoder log at {} and {} have the"
                    " same sequence '{}', dir '{}' and qp '{}', but different"
                    " absolute paths."
                ).format(old_enc_log.path, enc_log.path, enc_log.sequence,
                         enc_log.config, enc_log.qp))

        self._tree[enc_log.sequence][enc_log.config][enc_log.qp] = enc_log
        self._flat[enc_log.path] = enc_log

        self._update_views(self._tree)

    def update(self, enc_logs):
        """Adds all elements in the iterable :param: `enc_logs` to the
           collection"""
        for enc_log in enc_logs:
            self.add(enc_log)

    @classmethod
    def _flatten_dict_tree(cls, parent, depth=0):
        """Helper function to create a flatted list from a dictionary tree."""
        if depth >= cls._max_tree_depth:
            raise Exception("Maximal tree depth exceeded")
        if isinstance(parent, EncLog):
            return [parent]

        enc_logs = []
        for child in parent.values():
            enc_logs.extend( cls._flatten_dict_tree(child, depth = depth + 1) )
        return enc_logs

    def get_by_sequence(self, sequence):
        #Access a sequence in the EncLog tree and flatten the remaining tree
        return self._flatten_dict_tree( self._tree[sequence] )

    def get_by_tree_keys(self, sequence, config, qp):
        return self._tree[sequence][config][qp]

    def __getitem__(self, path):
        """Access element by path ie. unique identifier"""
        return self._flat[path]

    def __iter__(self):
        return iter(self._flat)

    def __contains__(self, enc_log):
        return enc_log.path in self._flat

    def __len__(self):
        return len(self._flat)

    def __str__(self):
        return str(list(self))

    def __repr__(self):
        return str(self)
        
