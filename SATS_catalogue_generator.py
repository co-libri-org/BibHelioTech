import os
import re
from datetime import *

main_path = "./DATA/Papers"

SATS_dict = {}

for folders in os.listdir(main_path):
    sub_folders = os.path.join(main_path, folders)
    for sub_sub_folders in os.listdir(sub_folders):
        files_path = os.path.join(sub_folders, sub_sub_folders)
        for files in os.listdir(files_path):
            if files.endswith("bibheliotech_V1.txt"):
                liste = []
                with open(os.path.join(files_path,files)) as file:
                    Lines = file.readlines()
                    for line in Lines:
                        if not re.search("^#",line): # skip comments lines
                            sat = line.split(" ")[3].replace("\"","") # delete " from satellites name
                            # group by satellites
                            if sat not in SATS_dict:
                                SATS_dict[sat] = []
                                the_line = [things.replace("\"", "") for things in line.split(" ")]
                                SATS_dict[sat].append({'start_time': the_line[0],
                                                       'stop_time': the_line[1],
                                                       'DOI': the_line[2],
                                                       'sat': the_line[3],
                                                       'inst': the_line[4],
                                                       'reg': the_line[5]})
                            else:
                                the_line = [things.replace("\"", "") for things in line.split(" ")]
                                SATS_dict[sat].append({'start_time': the_line[0],
                                                       'stop_time': the_line[1],
                                                       'DOI': the_line[2],
                                                       'sat': the_line[3],
                                                       'inst': the_line[4],
                                                       'reg': the_line[5]})

for elems,val in SATS_dict.items():
    SATS_dict[elems] = sorted(val, key=lambda d: d['start_time']) # sort by ascending start_time

# write datas
for elems,val in SATS_dict.items():
    with open("./DATA/SATS_catalogues/" +elems+"_bibheliotech.txt", "w") as f:
        f.write("# Name: ascii_cat;" + "\n")
        f.write("# Creation Date: " + datetime.now().isoformat() + ";" + "\n")
        f.write("# Description: Catalogue of events resulting from the HelioNER code (Dablanc & Génot, "+ "\"https://github.com/ADablanc/BibHelioTech.git\"" +") on the papers mentionning "+elems+" as listed in the third column by their DOI. The two first columns are the start/stop times of the event; the fourth column is the "+elems+" with the list of instruments (1 or more) listed in the fifth column. The sixth column is the most probable region of space where the observation took place (SPASE ObservedRegions term).\n")
        f.write("# Parameter 1: id:column1; name:DOI; size:1; type:char;" + "\n")
        f.write("# Parameter 2: id:column2; name:SATS; size:1; type:char;" + "\n")
        f.write("# Parameter 3: id:column3; name:INSTS; size:1; type:char;" + "\n")
        f.write("# Parameter 4: id:column4; name:REGS; size:1; type:char;" + "\n")
        for elements in val:
            f.write(elements['start_time'] + " " + elements['stop_time'] + " " + elements['DOI'] + " " + "\"" + elements['sat'] + "\"" + " " + "\"" + elements['inst'] + "\"" + " " + "\"" + elements['reg'].replace('\n','') + "\"" + "\n")
