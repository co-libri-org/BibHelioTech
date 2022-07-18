from datetime import datetime
start_time = datetime.now()

import os
import re
import shutil

from A_OCRiser import *
from A_OCR_filtering import *
from A_SUTime_processing import *
from A_Entities_finder import *
from A_GROBID_generator import *

# os.chdir("../../grobid-0.7.1/")
# os.popen("./gradlew run")
# os.chdir("../Stage/Programmes/")
#
# sutime = SUTime(mark_time_ranges=True, include_range=True) # load sutime wrapper 22

main_path = "./DATA/Papers"

for folders in os.listdir(main_path):
    sub_folders = os.path.join(main_path, folders)
    for sub_sub_folders in os.listdir(sub_folders):
        if sub_sub_folders.endswith(".pdf"):
            os.makedirs(os.path.join(sub_folders,sub_sub_folders.replace(".pdf", "")))  # create the directory
            shutil.move(os.path.join(sub_folders,sub_sub_folders), os.path.join(sub_folders,sub_sub_folders.replace(".pdf", "")))
        pdf_paths = os.path.join(sub_folders,sub_sub_folders.replace(".pdf", ""))
        for pdf_files in os.listdir(pdf_paths):
            if pdf_files.endswith(".pdf"):
                print(os.path.join(sub_folders,sub_sub_folders))
                folder_name = pdf_files.replace(".pdf", "")
                if len(os.listdir(pdf_paths)) == 1: # check if the directory of the same name of the file exist (case not exist)
                    pdf_paths = os.path.join(pdf_paths)

                    PDF_file = os.path.join(pdf_paths,pdf_files)

                    PDF_OCRiser(pdf_paths, PDF_file) # OCR the pdf file

                    GROBID_generation(pdf_paths)  # generate the XML GROBID file

                    filter(pdf_paths) # filter result of the OCR to deletes references, change HHmm4 to HH:mm, etc ...
                    SUTime_treatement(pdf_paths, sutime) # SUTime read all the file and save its results in a file "res_sutime.json"
                    SUTime_transform(pdf_paths) # transforms some results of sutime to complete missing, etc ... save results in "res_sutime_2.json"
                    entities_finder(pdf_paths)
                else:
                    pdf_paths = os.path.join(pdf_paths)

                    # filter(pdf_paths) # filter result of the OCR to deletes references, change HHmm to HH:mm, etc ...
                    # SUTime_treatement(pdf_paths,sutime) # SUTime read all the file and save its results in a file "res_sutime.json"
                    SUTime_transform(pdf_paths) # transforms some results of sutime to complete missing, etc ... save results in "res_sutime_2.json"
                    entities_finder(pdf_paths)

# os.chdir("../../grobid-0.7.1/")
# os.popen("./gradlew --stop")
# os.chdir("../Stage/Programmes/")

end_time = datetime.now()
print("TOTAL ELAPSED TIME: ---"+str(end_time - start_time)+"---")
