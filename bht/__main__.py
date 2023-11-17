import argparse
import glob
import os
from datetime import datetime

from bht.pipeline import bht_run_file, bht_run_dir, run_pipeline, PipeStep
from bht_config import yml_settings
from web.istex_proxy import istex_id_to_url, IstexDoctype, get_file_from_id

if __name__ == '__main__':

    start_time = datetime.now()

    papers_dir = yml_settings["BHT_PAPERS_DIR"]

    # main_logger = initLogger(os.path.join(BHT_ROOT, 'sw2_main.log'))

    # PARSE COMMAND LINE
    parser = argparse.ArgumentParser(description="""
    Entrypoint to run the bibheliotech pdf papers parser
    """,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-i', '--istex-id', type=str,
                        help='Run pipeline on document from ISTEX id. (dont grobid or ocr)')
    parser.add_argument('-d', '--pdf-dir', type=str,
                        help='One pdf dir to make catalog from')
    parser.add_argument('-f', '--pdf-file', type=str,
                        help='One pdf file to make catalog from')
    parser.add_argument('-p', '--parse-dir', dest='parse_dir', action='store_true',
                        help='Parse base dir and show content')
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
        import sys

        sys.exit()
    if args.pdf_file:
        bht_run_file(args.pdf_file, papers_dir)
    elif args.pdf_dir:
        bht_run_dir(args.pdf_dir)
    elif args.istex_id:
        doc_type = IstexDoctype.TXT
        content, filename = get_file_from_id(args.istex_id, doc_type)
        filepath = os.path.join(yml_settings["BHT_DATA_DIR"], filename)
        with open(filepath, "wb") as binary_file:
            # Write bytes to file
            binary_file.write(content)
        print(f"Written to {filepath}")
        done_steps = run_pipeline(filepath,
                                  doc_type,
                                  pipe_steps=[PipeStep.MKDIR, PipeStep.FILTER, PipeStep.SUTIME, PipeStep.ENTITIES])
        # print(f'Steps done {",".join(done_steps)}')

    end_time = datetime.now()
    print("TOTAL ELAPSED TIME: ---" + str(end_time - start_time) + "---")
