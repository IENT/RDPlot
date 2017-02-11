from model import (EncLog, EncLogParserError)

from os.path import (basename,sep, normpath)
import re

class EncLogHM(EncLog):
    def __init__(self, path):
        super().__init__(path)

    def _parse_path(self, path):
        try:
            # Assumes structure of .../<simulation_directory>/log/<basename>
            directories = normpath(path).split(sep)[0: -2]
            filename = basename(path)
        except IndexError:
            raise EncLogParserError(
                "Path {} can not be splitted into directories and filename"
                    .format(filename, path)
            )

        try:
            seperator = '-'
            filename_splitted = filename.split('_QP')[0].split(seperator)

            sequence = filename_splitted[-1]
            config = seperator.join(filename_splitted[0: -2])
        except IndexError:
            raise EncLogParserError((
                            "Filename {} can not be splitted into config until '{}' and"
                            " sequence between last '{}' and '_QP'"
                        ).format(filename, seperator, seperator))

        # prepend simulation directory to config
        config = directories[-1] + ' ' + config
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            qp = re.findall(r""" ^QP \s+ : \s+ (\d+.\d+) $
                                  """, log_text, re.M + re.X)
        qp = qp[0]
        return sequence, config, qp


    def _parse_summary_data(self):
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            summaries = re.findall(r""" ^(\w*)-*.*$ # catch summary line
                           \s* # catch newline and space
                           (.*)\| # catch phrase Total Frames / I / P / B
                           (\s+\S+)(\s+\S+)(\s+\S+)(\s+\S+)(\s+\S+)# catch rest of the line
                           \s* # catch newline and space
                           (\d+\s+)\w # catch frame number
                           (\s+\d+\.\d+)(\s+\d+\.\d+)(\s+\d+\.\d+)(\s+\d+\.\d+)(\s+\d+\.\d+) # catch the fractional number (rate, PSNRs)
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

            name_rate = 'Bitrate'
            names.remove('Bitrate')

            # now pack everything together
            for name in names:
                if name not in data[summary_type]:  # create upon first access
                    data[summary_type][name] = []
                # Reference all data to *self.qp*
                data[summary_type][name].append(
                    (name_val_dict[name_rate], name_val_dict[name])
                )
        return data

    def _parse_temporal_data(self):
        # this function extracts temporal values
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file

        tempData = re.findall(r"""
            ^POC \s+ (\d+) \s+ .+ \s+ \d+ \s+ . \s+ (.-\D+) ,  #Slice
            \s .+ \) \s+ (\d+) \s+ (.+) \s+ \[ (\D+) \s+ (\d+.\d+) \s+ #Y PSNR
            \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ # U PSNR
            \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ # v PSNR
            """, log_text, re.M + re.X)

        # Association between index of data in tempData and corresponding
        # output key. Output shape definition is in one place.
        names = {0: 'Frames', 2: 'Bits', 5: 'Y-PSNR', 7: 'U-PSNR',
                 9: 'V-PSNR'}

        # Define output data dict and fill it with parsed values
        data = {name: [] for (index, name) in names.items()}
        for i in range(0, len(tempData)):
            # As referencing to frame produces error, reference to index *i*
            for (index, name) in names.items():
                data[name].append(
                    (i, tempData[i][index])
                )
        return data