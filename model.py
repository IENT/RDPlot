import re


class Sequence():
    """"Keeps all information on a sequence.
    The appropriate encoder logs are processed once, extracting all relevant information.
    Offers methods for extracting the information from the logs.
    """

    def __init__(self, sequence_name_common, sequence_files):
        self.log_files = {}
        self.name = ""
        self.qp_vals = []
        self.sequence_files = {}  # will fill this with the list sequence_files with qp as key after they are extracted
        self.summary_data = {}
        self.temporal_data = {}

        self.name = sequence_name_common
        self.extract_qp_vals(sequence_files)
        self.extract_rd_vals()
        self.extract_temporal_vals()

    def extract_qp_vals(self, sequence_files):
        for sequence_file in sequence_files:
            m = re.search(r'_QP(\d*)_', sequence_file)
            if m:
                qp_val = m.group(1)
                self.qp_vals.append(qp_val)
                self.sequence_files[qp_val] = sequence_file
            else:
                print('No match for QP value in sequence name')  # todo: notify user, exception?
        self.qp_vals.sort(reverse=True)

    def extract_temporal_vals(self):
        #this function extracts temporal values
        for qp in self.qp_vals:
            file = self.sequence_files[qp]
        # for (qp, file) in self.sequence_files.items():
            with open(file, 'r') as log_file:
                log_text = log_file.read()  # reads the whole text file
                summaries_qp = re.findall(r"""
                    POC \s+ (\d+) \s+ .+ \s+ \d+ \s+ . \s+ (.-\D+) ,  #Slice
                    \s .+ \) \s+ (\d+) \s+ (.+) \s+ \[ (\D+) \s+ (\d+.\d+) \s+ #Y PSNR
                    \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ # U PSNR
                    \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ # v PSNR
                    """, log_text, re.M + re.X)
                frames = []
                yPsnr = []
                uPsnr = []
                vPsnr = []
                #slice = []
                rate = []
                for i in range(0, len(summaries_qp)):
                    frames.append(summaries_qp[i][0])
                    #slice.append(summaries_qp[i][1])
                    rate.append(summaries_qp[i][2])
                    yPsnr.append(summaries_qp[i][5])
                    uPsnr.append(summaries_qp[i][7])
                    vPsnr.append(summaries_qp[i][9])
                tempdata = {'Frame': frames, 'Bits': rate,
                        'Y-PSNR': yPsnr, 'U-PSNR': uPsnr, 'V-PSNR': vPsnr}
                self.temporal_data[qp] = tempdata

    def extract_rd_vals(self):
        """
        This functions find all data matching the Regex format specified below and stores it in dicts in the sequence.
        Care was taken to avoid coding explicit names, like 'Y-PSNR', 'YUV-PSNR', etc...
        """
        for qp in self.qp_vals:
            file = self.sequence_files[qp]
        # for (qp, file) in self.sequence_files.items():
            with open(file, 'r') as log_file:
                log_text = log_file.read()  # reads the whole text file
                summaries_qp = re.findall(r"""  ^(\w*)-*.*$ # catch summary line
                               \s* # catch newline and space
                               (.*)\| # catch phrase Total Frames / I / P / B
                               (\s*\S*)(\s*\S*)(\s*\S*)(\s*\S*)(\s*\S*)# catch rest of the line
                               \s* # catch newline and space
                               (\d*\s*)\w # catch frame number
                               (\s*\d*\.\d*)(\s*\d*\.\d*)(\s*\d*\.\d*)(\s*\d*\.\d*)(\s*\d*\.\d*) # catch the fractional number (rate, PSNRs)
                          """, log_text, re.M + re.X)

                for summary in summaries_qp:
                    summary_type = summary[0]
                    if summary_type not in self.summary_data:  # create upon first access
                        self.summary_data[summary_type] = {}
                    names = summary[1:7]
                    vals = summary[7:]

                    names = [name.strip() for name in names]  # remove leading and trailing space
                    vals = [float(val) for val in vals]  # convert to numbers

                    name_val_dict = dict(zip(names, vals))  # pack both together in a dict
                    # print(summary_type)

                    # now pack everything together
                    for name in names:
                        if name not in self.summary_data[summary_type]: # create upon first access
                            self.summary_data[summary_type][name] = []
                        self.summary_data[summary_type][name].append(name_val_dict[name])
        
class EncData():
    def __init__(self, summary=None, temporal=None):
        if summary is None:
            summary = []
        self.summary = summary
                
        if temporal is None:
            temporal = []
        self.temporal = semporal

class EncLog():
    def __init__(self, path):
        #Path is unique identifier
        self.path = path
        #Additional identifiers
        #TODO dummy, should be properties, parsing should happen here
        self.sequence = ""
        self.config = ""
        self.qp = ""
        
        #Encoder log data which exist as summary and temporal data
        self.yuvPsnr = EncData()
        self.yPsnr = EncData()
        self.uPsnr = EncData()
        self.vPsnr = EncData()
        
        #Encoder log data specific to temporal (T) or summary (S) 'domain'
        self.bitrateS = []
        self.bitsT = []
        self.sliceT = []
        
        # # the I represents I Slices Summary
        # self.yuvPsnrI = -1
        # self.yPsnrI = -1
        # self.uPsnrI = -1
        # self.vPsnrI = -1
        # self.bitrateI = -1
        #
        # # the P represents P Slices Summary
        # self.yuvPsnrP = -1
        # self.yPsnrP = -1
        # self.uPsnrP = -1
        # self.vPsnrP = -1
        # self.bitrateP = -1
        #
        # # the B represents B Slices Summary
        # self.yuvPsnrB = -1
        # self.yPsnrB = -1
        # self.uPsnrB = -1
        # self.vPsnrB = -1
        # self.bitrateB = -1

    def extract_temporal_values(self, sequenceName):
        #this function extracts temporal values
        with open(sequenceName, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            tempData = re.findall(r"""
                POC \s+ (\d+) \s+ .+ \s+ \d+ \s+ . \s+ (.-\D+) ,  #Slice
                \s .+ \) \s+ (\d+) \s+ (.+) \s+ \[ (\D+) \s+ (\d+.\d+) \s+ #Y PSNR
                \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ # U PSNR
                \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ # v PSNR
                """, log_text, re.M + re.X)

            for i in range(0, len(tempData)):
                self.sliceT.append(tempData[i][1])
                self.bitsT.append(tempData[i][2])
                self.yPsnr.temporal.append(tempData[i][5])
                self.uPsnr.temporal.append(tempData[i][7])
                self.vPsnr.temporal.append(tempData[i][9])


    def extract_summary_values(self, sequenceName):
        # this function extracts temporal values
        with open(sequenceName, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            tempData = re.findall(r""" Total \s Frames \D+
                        (\d+) \s+ \D \s+ (\S+) \s+ (\S+) # Y-PSNR
                        \s+ (\S+) \s+ (\S+) \s+ (\S+) # YUV-PSNR
                        """, log_text, re.M + re.X)

            for i in range(0, len(tempData)):
                self.frames.append(tempData[i][0])
                self.bitrateS.append(tempData[i][1])
                self.yPsnr.summary.append(tempData[i][2])
                self.uPsnr.summary.append(tempData[i][3])
                self.vPsnr.summary.append(tempData[i][4])
                self.yuvPsnr.summary.append(tempData[i][5])

    def __eq__(self, enc_log):
        return self.path == enc_log.path
        
class EncLogCollection():
    """Collection of :class: `model.EncLog`s. The class implements different
       access/iteration/etc. methods. Additionally it implements parsing the
       file system for certain encoder logs eg. all encoder logs of one sequence
       in different folders."""
    def __init__(self, enc_logs=None):
        #References to the encoder logs are stored in a flat dictionary using
        #the path/unique identifier as key and a tree using sequence, config and 
        #qp as key
        self._flat = {} 
        self._tree = {}
        if enc_logs is None:
            enc_logs = []
        self.update(enc_logs)
    
    def add(self, enc_log):
        """Adds :param: `enc_log` to the collection or replaces it if it is
           already in the collection."""
        self._flat[enc_log.path] = enc_log
            
        #Eventually the tree has to be extended if new sequences are added ie.
        #additionaly dictionaries have to be inserted before the encoder log can
        #be appended
        if enc_log.sequence not in self._tree:
            self._tree[enc_log.sequence] = {}
        else if enc_log.config not in self._tree[enc_log.sequence]:
            self._tree[enc_log.config] = {}

        self._tree[enc_log.sequence][enc_log.config][enc_log.qp]
    
    def update(self, enc_logs):
        """Adds all elements in the iterable :param: `enc_logs` to the
           collection"""
        for enc_log in enc_logs:
            if enc_log in self:
                raise ReloadError()
            self.set_enc_log(enc_log)
    
    def __getitem__(self, first_key, second_key=None, third_key=None):
        """Try accessing by using sequence, config and id or path."""
        #TODO This is kind of the pythonic way, but probably very inefficient in
        #case of linear indecies
        
        try:
            #Interpret keys as sequence, config and qp
            return self._tree[first_key][second_key][third_key]
        except KeyError:
            pass
            
        try:
            #Interpret first_key as path ie. unique identifier
            return self._flat[first_key]
        except KeyError:
            raise KeyError((
                "Could neither interpret (first_key={}, second_key={},"
                " {third_key={}) as (sequence, config, qp) nor (path, _, _)"
            ).format(first_key, second_key, third_key)))
    
    def __iter__(self):
        iter(self._flat)
        
    def __contains__(self, enc_log):
        return enc_log.path in self._flat
    
    def __len__(self):
        return len(self._flat)
    
    def __str__(self):
        return str(list(self))
        
    def __repr__(self):
        return str(self)
