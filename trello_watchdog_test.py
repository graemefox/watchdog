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

parser = argparse.ArgumentParser(description='arguments for watch_for_new_proj_dirs')
parser.add_argument('-i','--input_dir', help='The directory you\'re watching for creation of new dirs', required=True)
parser.add_argument('-d','--db_dir', help='The dir in which to store the DB of modded directories', required=True)
args = parser.parse_args()

# give args snappy names
watch_dir = args.input_dir

deepseq_trello_db = args.db_dir

if __name__ == "__main__":
    patterns = ["*"]
#    ignore_patterns = None
    # ignore OSX hidden folders 
    ignore_patterns = ['^\.*', \
                       '.*/\..*']
    ignore_directories = False
    case_sensitive = True
    my_event_handler = PatternMatchingEventHandler(patterns, \
                           ignore_patterns, \
                           ignore_directories, \
                           case_sensitive)

def parse_quote(quote_docx, \
                trello_data, \
                project, \
                trello_db, \
                quote_file):
    try:
        doc = zipfile.ZipFile(quote_docx).read('word/document.xml')
        root = ET.fromstring(doc)
        ET.tostring(root)
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        body = root.find('w:body', ns)  # find the XML "body" tag
        p_sections = body.findall('w:p', ns)  # under the body tag, find all the paragraph sections
        ### this will go through the document line by line
        for p in p_sections:
            text_elems = p.findall('.//w:t', ns)
            line = ''.join([t.text for t in text_elems])
            if "PREPARED BY:" in line:
                try:
                    prepared_by = line.strip().split("PREPARED BY: ")[1]
                    trello_db[project]["quote_prepared_by"] = str(prepared_by)
                except:
                    pass
            if "REF:" in line:
                try:
                    quote_ref = line.strip().split("REF: ")[1]
                    trello_db[project]["quote_ref_full_name"] = str(quote_ref)
                except:
                    pass
            if " DATE:" in line:
                try:
                    quote_date = line.strip().split("DATE: ")[1]
                    trello_db[project]["quote_prepared_date"] = str(quote_date)
                except:
                    pass
            if "PROJECT:" in line:
                try:
                    proj_title = line.strip().split("PROJECT: ")[1]
                    trello_db[project]["project_title"] = str(proj_title)
                except:
                    pass
        trello_db[project]["quote"] = str(quote_file)
        write_to_proj_data_file(trello_db, project)
    except:
        pass
    return(trello_db)

def parse_additional_info_xlsx(additional_info_sheet, \
                               trello_data_file, \
                               project, \
                               trello_db, \
                               additionalinfofile):
    try:
        workbook = pd.read_excel(additional_info_sheet)
        customer_contact = workbook['Data'].loc[1]
        trello_db[project]["customer_contact_details"] = str(customer_contact)
        customer_site = workbook['Data'].loc[2]
        trello_db[project]["customer_site"] = str(customer_site)
        date_samples_arrived = workbook['Data'].loc[3]
        try:
            trello_db[project]["date_samples_arrived"] = f"{date_samples_arrived:%Y-%m-%d}"
        except:
            pass
        SOLS_guess_hours = workbook['Data'].loc[4]
        trello_db[project]["if_SoLS_guestimated_hours_uncharged"] = str(SOLS_guess_hours)
        accepted = workbook['Data'].loc[5]
        try:
            trello_db[project]["acceptance_in_date"] = f"{accepted:%Y-%m-%d}"
        except:
            pass
        analysis_inc = workbook['Data'].loc[6]
        trello_db[project]["analysis_included"] = str(analysis_inc)
        turnaround = workbook['Data'].loc[7]
        trello_db[project]["quoted_turnaround_time"] = str(turnaround)
        CDA_legals = workbook['Data'].loc[8]
        trello_db[project]["CDA_legal_docs_in_place"] = str(CDA_legals)
        CDA_reference = workbook['Data'].loc[9]
        trello_db[project]["CDA_reference"] = str(CDA_reference)
        samples_UK = workbook['Data'].loc[10]
        trello_db[project]["Samples_from_UK"] = str(samples_UK)
        trusted_research_req = workbook['Data'].loc[11]
        trello_db[project]["Trusted_Research_Required"] = str(trusted_research_req)
        trusted_research_outcome = workbook['Data'].loc[12]
        trello_db[project]["Trusted_Research_Outcome"] = str(trusted_research_outcome)
        platform = workbook['Data'].loc[13]
        trello_db[project]["platform_type"] = str(platform)
        proj_type = workbook['Data'].loc[14]
        trello_db[project]["simple_type_of_project"] = str(proj_type)
        sample_no = workbook['Data'].loc[15] 
        trello_db[project]["number_of_samples"] = str(sample_no)
        revised = workbook['Data'].loc[16]
        try:
            trello_db[project]["quote_generation_date_revision_date"] = f"{revised:%Y-%m-%d}"
            trello_db[project]["quote_prepared_date"] = f"{revised:%Y-%m-%d}"
        except:
            pass
        bioinformatician = workbook['Data'].loc[17]
        trello_db[project]["bioinformatician_responsible"] = str(bioinformatician)
        sent_to_bioinformatics = workbook['Data'].loc[18]
        try:
            trello_db[project]["date_samples_were_delivered_to_bioinformatician"] = f"{sent_to_bioinformatics:%Y-%m-%d}"
        except:
            pass
        actual_turnaround = workbook['Data'].loc[19]
        trello_db[project]["actual_turn_around_time"] = str(actual_turnaround)
        trello = workbook['Data'].loc[20]
        trello_db[project]["trello"] = str(trello)
        trello_db[project]["additional_info"] = str(additionalinfofile)
        write_to_proj_data_file(trello_db, project)
    except:
        pass
    return(trello_db)

def parse_bioinformatics_info_xlsx(bioinformatics_info_sheet, \
                                   trello_data_file, \
                                   project, \
                                   trello_db, \
                                   bioinformaticsinfofile):
    try:
        workbook = pd.read_excel(bioinformatics_info_sheet)
        bioinf_complete = workbook['Data'].loc[1]
        try:
            trello_db[project]["date_bioinformatics_completed"] = f"{bioinf_complete:%Y-%m-%d}"
        except:
            pass
        date_report_sent = workbook['Data'].loc[2]
        try:
            trello_db[project]["report_sent_date"] = f"{date_report_sent:%Y-%m-%d}"
        except:
            pass
        date_azure_sent = workbook['Data'].loc[3]
        try:
            trello_db[project]["azure_data_download_date_sent"] = f"{date_azure_sent:%Y-%m-%d}"
        except:
            pass
        date_confirmed_backup = workbook['Data'].loc[4]
        try:
            trello_db[project]["date_data_confirmed_backed_up_by_client"] = f"{date_confirmed_backup:%Y-%m-%d}"
        except:
            pass
        date_local_data_delete = workbook['Data'].loc[5]
        try:
            trello_db[project]["date_data_deleted"] = f"{date_local_data_delete:%Y-%m-%d}"
        except:
            pass
        partial = workbook['Data'].loc[6]
        trello_db[project]["project_partially_complete"] = str(partial)
        partial_details = workbook['Data'].loc[7]
        trello_db[project]["partial_complete_details"] = str(partial_details)
        bioinf_notes = workbook['Data'].loc[8]
        trello_db[project]["bioinformatics_notes"] = str(bioinf_notes)
        # write to the appropriate project file
        write_to_proj_data_file(trello_db, project)
    except:
        pass
    return(trello_db)

def parse_sample_info_xlsx(sample_info_sheet, \
                           trello_data_file, \
                           project, \
                           trello_db, \
                           sampleinfofile):
    try:
        workbook = pd.read_excel(sample_info_sheet)
        quote_ID = workbook['Data'].loc[0]
        trello_db[project]["deepseq_quote_ID_unique_key"] = str(quote_ID)
        lab_person = workbook['Data'].loc[1]
        trello_db[project]["lab_team_member_responsible"] = str(lab_person)
        QC_started = workbook['Data'].loc[2]
        try:
            trello_db[project]["date_lab_QC_started"] = f"{QC_started:%Y-%m-%d}"
        except:
            pass
        lib_started = workbook['Data'].loc[3]
        try:
            trello_db[project]["date_lib_prep_started"] = f"{lib_started:%Y-%m-%d}"
        except:
            pass
        lab_complete = workbook['Data'].loc[4]
        try:
            trello_db[project]["date_samples_completed_in_lab"] = f"{lab_complete:%Y-%m-%d}"
        except:
            pass
        library_prep = workbook['Data'].loc[5]
        trello_db[project]["library_prep"] = str(library_prep)
        customer = workbook['Data'].loc[6]
        trello_db[project]["customer"] = str(customer)
        flowcell = workbook['Data'].loc[7]
        trello_db[project]["flowcell"] = str(flowcell)
        # write to the appropriate project file
        trello_db[project]["sample_info"] = str(sampleinfofile)
        write_to_proj_data_file(trello_db, project)
    except:
        pass
    return(trello_db)

def curr_proj_file_to_dict(project):
    proj_dict = {}
    with open(path_to_proj_data_file(project), 'r') as proj_data_file:
        for row in proj_data_file:
            proj_dict[row.split(",")[0]] = row.split(",")[1].rstrip("\n")
    proj_data_file.close()
    return(proj_dict)

def path_to_proj_data_file(project):
    path = watch_dir \
           + project \
           + "/" \
           + project \
           + "_trello/" \
           + project \
           + "_trello_data.csv"
    return(path)

def write_to_proj_data_file(trello_db, project):
    update = False
    # read the current v of a projects data
    proj_dict = curr_proj_file_to_dict(project)
    # should have some new data because have read a file
    for key in proj_dict.keys():
        if key in trello_db[project]:
            # if found something parsing the info sheets that is not currently in the DB
            if not proj_dict[key] == trello_db[project][key] and not trello_db[project][key] == "NA":
                proj_dict[key] = trello_db[project][key]
                update = True
            # if found an update to the CSV which is not in the info sheets
            # the CSV sheet is ahead of parsed info (been updated)
            if not proj_dict[key] == trello_db[project][key] \
                and not proj_dict[key] == "NA":
                # update the DB with the value from the CSV
                trello_db[project][key] = proj_dict[key]
                update = True
    if update:
        with open(path_to_proj_data_file(project), 'w') as proj_data_file:
           for key in proj_dict:
               proj_data_file.write(key + "," + str(proj_dict[key])+"\n")
        proj_data_file.close()
        with open(deepseq_trello_db + "trello.pickle", 'wb') as pickle_out:
            pickle.dump(trello_db, pickle_out)
    return()

def backup_trello_pickle():
    # TODO some kind of scheduler for this to happen.
    shutil.copy("/data/graeme/trello_scripts/db/trello.pickle", \
                "/data/graeme/trello_scripts/db_backups/" \
                + str(datetime.now()) + "_trello.pickle")

def copy_template_file_to_new_proj(new_dir):
    shutil.copy("/data/graeme/trello_scripts/template_files/trello_data_template.csv", \
                 path_to_proj_data_file(new_dir))
    ## and add the blank info the main DB
    proj_dict = {}
    with open(path_to_proj_data_file(new_dir), 'r') as proj_data_file:
        for row in proj_data_file:
            proj_dict[row.split(",")[0]] = row.split(",")[1].rstrip("\n")
    proj_data_file.close()
    return(proj_dict)

def does_pickle_db_exist():
    exists = False
    curr_db = False
    if os.path.isfile(deepseq_trello_db + "trello.pickle"):
        exists = True
        with open(deepseq_trello_db + "trello.pickle", 'rb') as pickle_in:
            curr_db = pickle.load(pickle_in)
    return(exists)

def setup_new_trello_db():
    print("new trello DB")
    trello_db = {}
    for directory in os.listdir(watch_dir):
        trello_db = {
            directory : {
            }
        }
        # create a brand new trello db
        trello_subdir =  watch_dir + directory + "/" + directory + "_trello" 
        if os.path.isdir(watch_dir + directory) and "untitled folder" not in directory:
            os.mkdir(trello_subdir)
            proj_dict = copy_template_file_to_new_proj(directory)
            trello_db[directory] = proj_dict
            trello_db[directory]['directory'] = directory
            with open(deepseq_trello_db + "trello.pickle", 'wb') as pickle_out:
               pickle.dump(trello_db, pickle_out)
    return(trello_db)

def check_for_removed_dir():
    return()

def check_for_new_proj_subdir():
    update = False
    with open(deepseq_trello_db + "trello.pickle", 'rb') as handle:
        current_db = pickle.load(handle)
        for directory in os.listdir(args.input_dir):
            # if a directory we have seen before
            if directory in current_db.keys():
                continue
            else:
                # something new has appeared
                # if it is not a directory, do nothing
                if os.path.isdir(watch_dir + directory):
                    # create the trello subdir and copy in the template
                    trello_subdir =  watch_dir + directory + "/" + directory + "_trello"
                    # ignore OSX's default "untitled folder"
                    if "untitled folder" not in directory:
                        try:
                            os.mkdir(trello_subdir)
                            # get the new empty dict from the new file
                            proj_dict = copy_template_file_to_new_proj(directory)
                            current_db[directory] = proj_dict
                            current_db[directory]['directory'] = directory
                            update = True
                        except:
                            pass
    if update:
        with open(deepseq_trello_db + "trello.pickle", 'wb') as pickle_out:
            pickle.dump(current_db, pickle_out)
            pickle_out.close()
    return(current_db) # the updated db

def check_for_quote(trello_db):
    for directory in os.listdir(watch_dir):
        # check it is a dir not a misplaced file
        if os.path.isdir(watch_dir + directory):
            for file in os.listdir(watch_dir + directory):
                if bool(re.search("^DeepSeq.*docx$", file, re.IGNORECASE)):
                    print("Found quote")
                    quote=re.search("^DeepSeq.*docx$", file, re.IGNORECASE)
                    trello_db = parse_quote(watch_dir + directory + "/" + file, \
                                path_to_proj_data_file(directory),
                                directory,
                                trello_db,
                                quote.group())
    return(trello_db)

def check_for_sample_info(trello_db):
    for directory in os.listdir(watch_dir):
        # check it is a directory and not a misplaced file
        if os.path.isdir(watch_dir + directory):
            for file in os.listdir(watch_dir + directory):
                if bool(re.search(".*_Sample_Information.xlsx", file, re.IGNORECASE)):
                    print("Found sample info")
                    sampleinfo=re.search(".*_Sample_Information.xlsx", file, re.IGNORECASE)
                    trello_db = parse_sample_info_xlsx(watch_dir + directory + "/" + file, \
                                path_to_proj_data_file(directory),
                                directory,
                                trello_db,
                                sampleinfo.group())
    return(trello_db)

def check_for_additional_info(trello_db):
    for directory in os.listdir(watch_dir):
        # check it is a dir not a misplaced file
        if os.path.isdir(watch_dir + directory):
            for file in os.listdir(watch_dir + directory):
                if bool(re.search(".*_Additional_Information.xlsx", file, re.IGNORECASE)):
                    print("Found additional info")
                    additionalinfo=re.search(".*_Additional_Information.xlsx", file, re.IGNORECASE)
                    parse_additional_info_xlsx(watch_dir + directory + "/" + file, \
                                               path_to_proj_data_file(directory),
                                               directory,
                                               trello_db,
                                               additionalinfo.group())
    return(trello_db)

def check_for_bioinformatics_info(trello_db):
    for directory in os.listdir(watch_dir):
        if os.path.isdir(watch_dir + directory):
            for file in os.listdir(watch_dir + directory):
                if bool(re.search(".*_Bioinformatics.xlsx", file, re.IGNORECASE)):
                    print("Found bioinformatics info")
                    bioinformaticsinfo=re.search(".*_Bioinformatics.xlsx", file, re.IGNORECASE)
                    parse_bioinformatics_info_xlsx(watch_dir + directory + "/" + file, \
                                                   path_to_proj_data_file(directory), \
                                                   directory,
                                                   trello_db,
                                                   bioinformaticsinfo.group())
    return(trello_db)

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
    check_for_db = does_pickle_db_exist()
    if not check_for_db:
        # start a brand new trello DB
        trello_db = setup_new_trello_db()
        trello_db = check_for_quote(trello_db)
        trello_db = check_for_sample_info(trello_db)
        trello_db = check_for_bioinformatics_info(trello_db)
    else:
        # add to a pre-existing one
        trello_db = check_for_new_proj_subdir()
        # has a quote been added?
        trello_db = check_for_quote(trello_db)
        # check for sample info
        trello_db = check_for_sample_info(trello_db)
        # check for additional info
        # TODO - the check for add info is causing bioing details to be removed
        trello_db = check_for_additional_info(trello_db)
        # check for bioinformatics details sheet
        trello_db = check_for_bioinformatics_info(trello_db)

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
