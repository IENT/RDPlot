from model import (EncLog, EncLogParserError)

from os.path import (basename,sep, normpath)
import re

class EncLogSHM(EncLog):
    def __init__(self, path):
        super().__init__(path)

    def _parse_path(self,path):
        try:
            # Assumes structure of .../<simulation_directory>/log/<basename>
            directories = normpath(path).split(sep)[0: -2]
            filename    = basename(path)
        except IndexError:
            raise EncLogParserError(
                "Path {} can not be splitted into directories and filename"
                .format(filename, path)
            )

        try:
            seperator = '-'
            filename_splitted = filename.split('_QPL10')[0].split(seperator)
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
        return (sequence, config, qp)

    def _parse_summary_data(self):
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            summaries = re.findall(r"""
                        ^\s+ L (\d+) \s+ (\d+) \s+ \D \s+ # the next is bitrate
                        (\S+) \s+ (\S+) \s+ (\S+) \s+ (\S+) \s+ (\S+)
                        """, log_text, re.M + re.X)

        data = {}
        layerQuantity = int(len(summaries) / 4)
        headerNames = ['SUMMARY', 'I', 'P', 'B']
        names = {1: 'Frames', 2: 'Bitrate', 3: 'Y-PSNR', 4: 'U-PSNR',
                 5: 'V-PSNR', 6: 'YUV-PSNR'}

        for it in range(0, 4):  # iterate through Summary, I, P, B
            data2 = {}
            for layer in range(0, layerQuantity):  # iterate through layers
                layerstring = 'layer ' + str(layer)
                data2[layerstring] = {}
                data3 = {}
                bitrate = summaries[layerQuantity * it + layer][2]
                for (index, name) in names.items():
                    # convert string '-nan' to int 0 if necessary
                    data3[name] = []
                    if isinstance(bitrate, str) and (bitrate == '-nan'):
                        data3[name].append(
                            (float(0), float(0))
                        )
                    else:
                        data3[name].append(
                            (float(bitrate), float(summaries[layerQuantity * it + layer][index]))
                        )
                data2[layerstring] = data3
            data[headerNames[it]] = data2
        return data

    def _parse_temporal_data(self):
        #this function extracts temporal values
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            tempData = re.findall(r"""
                                ^POC \s+ (\d+) .+? : \s+ (\d+) .+ (\D-\D+) \s \D+,  #Slice
                                .+ \) \s+ (\d+) \s+ (.+) \s+ \[ (\D+) \s+ (\d+.\d+) \s+ #Y PSNR
                                \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ # U PSNR
                                \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ # v PSNR
                                """, log_text, re.M + re.X)


        #Association between index of data in tempData and corresponding
        #output key. Output shape definition is in one place.
        names = {0: 'Frames', 3: 'Bits', 6: 'Y-PSNR', 8: 'U-PSNR',
                 10: 'V-PSNR'}

        layerQuantity = int(max(tempData[i][1] for i in range(0, len(tempData)))) + 1
        layerQuantity = int(layerQuantity)
        data = {}
        for layer in range(0, layerQuantity):  # iterate through layers
            data2 = {name: [] for (index, name) in names.items()}
            for j in range(0, int(len(tempData)/layerQuantity)):  #iterate through frames (POCS)
                for (index, name) in names.items():
                    data2[name].append(
                        (j, tempData[layerQuantity*j+layer][index])
                    )
            layerstring = 'layer ' + str(layer)
            data[layerstring] = data2
        return data