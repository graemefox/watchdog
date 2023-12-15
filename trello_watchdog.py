# the systemd file is written to:
# /etc/systemd/system/trello_watchdog.service
# start the service with
# sudo systemctl start trello_watchdog.service

import time
import watchdog
import argparse
import os
import pickle
import shutil
import re
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
from watchdog.events import PatternMatchingEventHandler
from datetime import datetime

from watchdog_funcs import *

parser = argparse.ArgumentParser(description='arguments for watch_for_new_proj_dirs')
parser.add_argument('-i','--input_dir', \
                    help='The directory you\'re watching for creation of new dirs', \
                    required=True)
parser.add_argument('-d','--db_dir', \
                    help='The dir in which to store the DB of modded directories', \
                    required=True)
args = parser.parse_args()

# give args snappy names
watch_dir = args.input_dir
deepseq_trello_db = args.db_dir

if __name__ == "__main__":
    patterns = ["*"]
    # ignore OSX hidden folders 
    ignore_patterns = ['^\.*', \
                       '.*/\..*']
    ignore_directories = False
    case_sensitive = True
    my_event_handler = PatternMatchingEventHandler(patterns, \
                           ignore_patterns, \
                           ignore_directories, \
                           case_sensitive)

# probably not going to use created, or moved.
# deleted might be useful in the future....
def on_created(event):
    print(f"{event.src_path} has been created!")
    return()

def on_deleted(event):
#   print(f"{event.src_path} has been deleted!")
   return()

def on_moved(event):
#    print(f"{event.src_path} has been moved to {event.dest_path}")
    return()

def on_modified(event):
    time.sleep(1)
    check_for_db = does_pickle_db_exist(deepseq_trello_db)
    if not check_for_db:
        # start a brand new trello DB
        trello_db = setup_new_trello_db(watch_dir, deepseq_trello_db)
        trello_db = check_for_quote(trello_db, watch_dir, deepseq_trello_db)
        trello_db = check_for_sample_info(trello_db, watch_dir, deepseq_trello_db)
        trello_db = check_for_additional_info(trello_db, watch_dir, deepseq_trello_db)
        trello_db = check_for_bioinformatics_info(trello_db, watch_dir, deepseq_trello_db)
    else:
        trello_db = check_for_new_proj_subdir(deepseq_trello_db, watch_dir)
        # has a quote been added?
        trello_db = check_for_quote(trello_db, watch_dir, deepseq_trello_db)
        # check for sample info
        trello_db = check_for_sample_info(trello_db, watch_dir, deepseq_trello_db)
        # check for additional info
        trello_db = check_for_additional_info(trello_db, watch_dir, deepseq_trello_db)
        # check for bioinformatics details sheet
        trello_db = check_for_bioinformatics_info(trello_db, watch_dir, deepseq_trello_db)
        # check for any removed proj directories, and remove from the DB
        check_for_removed_dir(trello_db, deepseq_trello_db, watch_dir)

my_event_handler.on_created = on_created
my_event_handler.on_deleted = on_deleted
my_event_handler.on_modified = on_modified
my_event_handler.on_moved = on_moved

path = watch_dir
go_recursively = True
my_observer = PollingObserver()
my_observer.schedule(my_event_handler, \
                     path, \
                     recursive=go_recursively)

my_observer.start()
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    my_observer.stop()
    my_observer.join()
