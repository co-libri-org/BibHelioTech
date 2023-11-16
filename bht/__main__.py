import argparse
import glob
import os
from datetime import datetime

from bht.pipeline import bht_run_file, bht_run_dir
from bht_config import yml_settings

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
        bht_run_file(args.pdf_file, papers_dir)
    elif args.pdf_dir:
        bht_run_dir(args.pdf_dir)

    end_time = datetime.now()
    print("TOTAL ELAPSED TIME: ---" + str(end_time - start_time) + "---")
