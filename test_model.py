#!/usr/bin/python

from os.path import join
from os import listdir
from glob import glob

from pdb import set_trace
from matplotlib.pyplot import plot, show
from pprint import pprint

from model import (EncLog, EncLogCollection, summary_data_from_enc_logs,
                   sort_dict_of_lists_by_key)


#Assume a example simulation folder "simulation_example" in the parent of the
#project with subfolders containing simulation directories
PATH = "../simulation_examples"
#Fix config to specific directory
CONFIGS = ['HEVC']

SEQUENCE = ("HM16.7-Orig-glacier_vr_2880x1920_24_encoder+randomaccess+main"
            "_FTBE240_IBD8_IBD8")

def parse_configs():
    return list(EncLog.parse_directory(join(PATH, CONFIGS[0])))

def test_enc_log():
    encLogs = parse_configs()

    assert len(encLogs) == 40

    #Iterate over all summary data which should be present on all files
    for encLog in encLogs:
        summary = encLog.summary_data
        for key in ['SUMMARY', 'B', 'I']:
            data = summary[key]
            for k in ['Bitrate', 'Total Frames', 'U-PSNR', 'V-PSNR', 'Y-PSNR',
                      'YUV-PSNR']:
                int(data[k][0])

    sequence = encLogs[0].sequence
    summaries = summary_data_from_enc_logs(
        e for e in encLogs if e.sequence == sequence
    )
    for summary in summaries.values():
        summary = sort_dict_of_lists_by_key(summary, 'Bitrate')

def test_enc_log_collection():
    logs = parse_configs()
    
    #Create collection from first 10 logs
    log_collection = EncLogCollection(logs[1:10])

    #Add one log already present
    logs[1].test_property = True
    log_collection.add(logs[1])
    assert log_collection[logs[1].path].test_property == True
    #Add one element not already present
    log_collection.add(logs[15])
    assert logs[15] in log_collection

    #Readd some logs and add all remaining. Check if object now contains all
    #logs
    log_collection.update(logs)
    for path in log_collection:
        logs.remove(log_collection[path])
    assert len(logs) == 0
