import os
import shutil
from OCRiser import *
from OCR_filtering import *
from SUTime_processing import *
from Entities_finder import *
from GROBID_generator import *
from datetime import datetime
start_time = datetime.now()

os.chdir("../grobid-0.7.1/")
os.popen("./gradlew run") # starting GROBID server
os.chdir("../BibHelio_Tech/")

sutime = SUTime(mark_time_ranges=True, include_range=True) # load sutime wrapper

main_path = "./DATA/Papers"

for folders_or_pdf in os.listdir(main_path):
    folders_or_pdf_path = os.path.join(main_path, folders_or_pdf)
    if folders_or_pdf.endswith(".pdf"): # If '.pdf' on "Papers" folder --> paper not treated --> processing paper treatment.
        os.makedirs(os.path.join(main_path, folders_or_pdf.replace(".pdf", "")))  # create the directory under the same name than the paper.
        shutil.move(folders_or_pdf_path, os.path.join(main_path, folders_or_pdf.replace(".pdf", ""))) # move '.pdf' to his directory.
    pdf_paths = os.path.join(main_path, folders_or_pdf.replace(".pdf", ""))
    for pdf_files in os.listdir(pdf_paths): # precessing treatment.
        if pdf_files.endswith(".pdf"):
            print(pdf_paths)
            if len(os.listdir(pdf_paths)) == 1: # Only 1 file (the pdf) --> directory never treated --> processing first treatment.
                PDF_file = os.path.join(pdf_paths,pdf_files)
                PDF_OCRiser(pdf_paths, PDF_file) # OCR the pdf file
                GROBID_generation(pdf_paths)  # generate the XML GROBID file
                filter(pdf_paths) # filter result of the OCR to deletes references, change HHmm4 to HH:mm, etc ...
                SUTime_treatement(pdf_paths, sutime) # SUTime read all the file and save its results in a file "res_sutime.json"
                SUTime_transform(pdf_paths) # transforms some results of sutime to complete missing, etc ... save results in "res_sutime_2.json"
                entities_finder(pdf_paths) # entities recognition and association + writing of HPEvent
            else: # case directory already treated: processing only after GROBID generation. (comment to disable)
                filter(pdf_paths) # filter result of the OCR to deletes references, change HHmm to HH:mm, etc ...
                SUTime_treatement(pdf_paths,sutime) # SUTime read all the file and save its results in a file "res_sutime.json"
                SUTime_transform(pdf_paths) # transforms some results of sutime to complete missing, etc ... save results in "res_sutime_2.json"
                entities_finder(pdf_paths) # entities recognition and association + writing of HPEvent

os.chdir("../grobid-0.7.1/")
os.popen("./gradlew --stop") # stop GROBID server
os.chdir("../BibHelio_Tech/")

end_time = datetime.now()
print("TOTAL ELAPSED TIME: ---"+str(end_time - start_time)+"---")
