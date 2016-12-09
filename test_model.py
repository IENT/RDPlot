#!/usr/bin/python

from os.path import join
from os import listdir
from glob import glob

from model import EncLog, EncLogCollection


#Assume a example simulation folder "simulation_example" in the parent of the
#project with subfolders containing simulation directories
PATH = "../simulation_examples"
CONFIGS = listdir(PATH)


def parse_configs():
    for config in CONFIGS:
        config_path = join(PATH, config)
        
        return list(EncLog.parse_directory(config_path))

def test_enc_log():
    parse_configs()
        
def test_enc_log_collection():
    logs = parse_configs()
    
    log_collection = EncLogCollection(logs[1:3])
    log_collection.add(logs[4])
    log_collection.update(logs)
