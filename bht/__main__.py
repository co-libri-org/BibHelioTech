import argparse
import glob
import shutil
import os
from datetime import datetime

from bht.GROBID_generator import GROBID_generation
from bht.Entities_finder import entities_finder
from bht.OCRiser import PDF_OCRiser
from bht.OCR_filtering import ocr_filter
from bht.errors import *
from bht_config import yml_settings


def run_dir(_base_pdf_dir):
    for folders_or_pdf in os.listdir(_base_pdf_dir):
        folders_or_pdf_path = os.path.join(_base_pdf_dir, folders_or_pdf)
        if folders_or_pdf.endswith(
                ".pdf"):  # If '.pdf' on "Papers" folder --> paper not treated --> processing paper treatment.
            # create the directory under the same name than the paper.
            os.makedirs(os.path.join(_base_pdf_dir, folders_or_pdf.replace(".pdf", "")))
            # move '.pdf' to his directory.
            shutil.move(folders_or_pdf_path, os.path.join(_base_pdf_dir, folders_or_pdf.replace(".pdf", "")))
        pdf_paths = os.path.join(_base_pdf_dir, folders_or_pdf.replace(".pdf", ""))
        from bht.SUTime_processing import SUTime, SUTime_treatement, SUTime_transform
        sutime = SUTime(mark_time_ranges=True, include_range=True)  # load sutime wrapper
        for pdf_files in os.listdir(pdf_paths):  # processing treatment.
            if pdf_files.endswith(".pdf"):
                print(pdf_paths)
                # Only 1 file (the pdf) --> directory never treated --> processing first treatment.
                if len(os.listdir(pdf_paths)) == 1:
                    PDF_file = os.path.join(pdf_paths, pdf_files)
                    PDF_OCRiser(pdf_paths, PDF_file)  # OCR the pdf file
                    # generate the XML GROBID file
                    GROBID_generation(pdf_paths)
                    # filter result of the OCR to deletes references, change HHmm4 to HH:mm, etc ...
                    ocr_filter(pdf_paths)
                    # SUTime read all the file and save its results in a file "res_sutime.json"
                    SUTime_treatement(pdf_paths, sutime)
                    # transforms some results of sutime to complete missing, etc ... save results in "res_sutime_2.json"
                    SUTime_transform(pdf_paths)
                    # entities recognition and association + writing of HPEvent
                    entities_finder(pdf_paths)
                else:  # case directory already treated: processing only after GROBID generation. (COMMENT TO DISABLE)
                    # filter result of the OCR to deletes references, change HHmm to HH:mm, etc ...
                    ocr_filter(pdf_paths)
                    # SUTime read all the file and save its results in a file "res_sutime.json"
                    SUTime_treatement(pdf_paths, sutime)
                    # transforms some results of sutime to complete missing, etc ... save results in "res_sutime_2.json"
                    SUTime_transform(pdf_paths)
                    entities_finder(pdf_paths)  # entities recognition and association + writing of HPEvent


def run_file(orig_pdf_file, result_base_dir):

    # 0- Move original file to working directory
    pdf_filename = os.path.basename(orig_pdf_file)
    paper_name = pdf_filename.replace(".pdf", "")
    dest_pdf_dir = os.path.join(result_base_dir, paper_name)
    dest_pdf_file = os.path.join(dest_pdf_dir, pdf_filename)
    os.makedirs(dest_pdf_dir, exist_ok=True)
    shutil.copy(orig_pdf_file, dest_pdf_file)

    # 1- OCR the pdf file
    PDF_OCRiser(dest_pdf_dir, dest_pdf_file)

    # 2- Generate the XML GROBID file
    GROBID_generation(dest_pdf_dir)

    # 3- Sutime processing
    from bht.SUTime_processing import SUTime, SUTime_treatement, SUTime_transform

    sutime = SUTime(mark_time_ranges=True, include_range=True)  # load sutime wrapper
    # filter result of the OCR to deletes references, change HHmm4 to HH:mm, etc ...
    ocr_filter(dest_pdf_dir)
    # SUTime read all the file and save its results in a file "res_sutime.json"
    SUTime_treatement(dest_pdf_dir, sutime)
    # transforms some results of sutime to complete missing, etc ... save results in "res_sutime_2.json"
    SUTime_transform(dest_pdf_dir)
    # entities recognition and association + writing of HPEvent
    entities_finder(dest_pdf_dir)
    search_pattern = os.path.join(dest_pdf_dir, '**', '*bibheliotech*.txt')
    print(f"searching {search_pattern}")
    result_catalogs = glob.glob(search_pattern, recursive=True)
    found_file = result_catalogs[0]
    if not os.path.isfile(found_file):
        raise BhtResultError(f"No such file {found_file}")
    return found_file


if __name__ == '__main__':

    start_time = datetime.now()

    papers_dir = yml_settings["BHT_PAPERS_DIR"]

    # main_logger = initLogger(os.path.join(BHT_ROOT, 'sw2_main.log'))

    # PARSE COMMAND LINE
    parser = argparse.ArgumentParser(description="""
    Entrypoint to run the bibheliotech pdf papers parser
    """,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-d', '--pdf_dir', type=str,
                        help='One pdf dir to iterate through')
    parser.add_argument('-f', '--pdf_file', type=str,
                        help='One pdf file to parse')
    parser.add_argument('-p', '--parse-dir', dest='parse_dir', action='store_true',
                        help='Parse dir')
    args = parser.parse_args()

    if args.parse_dir:
        for item in os.listdir(papers_dir):
            abs_path = os.path.join(papers_dir, item)
            if os.path.isfile(abs_path):
                _f_type = "f"
            elif os.path.isdir(abs_path):
                _f_type = "d"
            else:
                _f_type = "u"

            print(_f_type, item)
        for item in glob.glob('*.py', root_dir="/home/richard/01DEV/BibHelioTech/bht/", recursive=True):
            print(item)
        import sys

        sys.exit()
    if args.pdf_file:
        run_file(args.pdf_file, papers_dir)
    elif args.pdf_dir:
        run_dir(args.pdf_dir)

    end_time = datetime.now()
    print("TOTAL ELAPSED TIME: ---" + str(end_time - start_time) + "---")
