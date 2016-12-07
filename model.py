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

class ParsedFile:
    def __init__(self):
        self.frames
        # the S represents summary, in this order: general summary, I,P,B summaries
        self.yuvPsnrS = []
        self.yPsnrS = []
        self.uPsnrS = []
        self.vPsnrS = []
        self.bitrateS = []

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

        # the T represents temporal Data
        self.yPsnrT = []
        self.uPsnrT = []
        self.vPsnrT = []
        self.bitsT = []
        self.sliceT = []

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
                self.yPsnrT.append(tempData[i][5])
                self.uPsnrT.append(tempData[i][7])
                self.vPsnrT.append(tempData[i][9])


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
                self.yPsnrS.append(tempData[i][2])
                self.uPsnrS.append(tempData[i][3])
                self.vPsnrS.append(tempData[i][4])
                self.yuvPsnrS.append(tempData[i][5])
