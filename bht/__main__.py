import argparse
import os
import sys
from datetime import datetime

from bht.pipeline import bht_run_file, run_pipeline, PipeStep
from bht_config import yml_settings

# TODO: REFACTOR dont import anything from web. to bht !!!!
from web.istex_proxy import IstexDoctype, get_file_from_id
from web.models import BhtFileType

if __name__ == "__main__":
    start_time = datetime.now()

    papers_dir = yml_settings["BHT_PAPERS_DIR"]

    # main_logger = initLogger(os.path.join(BHT_ROOT, 'sw2_main.log'))

    # PARSE COMMAND LINE
    parser = argparse.ArgumentParser(
        description="""
    Entrypoint to run the bibheliotech papers parser
    """,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-s",
        "--pipe-steps",
        dest="pipe_steps",
        help="Add pipeline steps to run in given directory.",
        choices=[ps.name for ps in list(PipeStep)],
        nargs="*",
    )
    parser.add_argument(
        "-i",
        "--istex-id",
        type=str,
        help="Run pipeline on txt document from ISTEX id. (dont grobid or ocr)",
    )
    parser.add_argument("-d", "--pipe-dir", type=str, help="Run pipeline on directory.")
    parser.add_argument(
        "-t",
        "--txt-file",
        type=str,
        help="Run pipeline on txt file (needs --doi to be set)",
    )
    parser.add_argument("--doi", type=str, help="Set DOI if txt")
    parser.add_argument("--pub-date", type=str, help="Set PublicationDate if txt")
    parser.add_argument(
        "-f", "--pdf-file", type=str, help="Run pipeline from pdf file."
    )
    parser.add_argument(
        "-b",
        "--base-dir",
        dest="base_dir",
        action="store_true",
        help="Show base directory content",
    )
    args = parser.parse_args()

    # Show the content of the base directory ( and exit)
    if args.base_dir:
        for item in os.listdir(papers_dir):
            abs_path = os.path.join(papers_dir, item)
            if os.path.isfile(abs_path):
                _f_type = "f"
            elif os.path.isdir(abs_path):
                _f_type = "d"
            else:
                _f_type = "u"

            print(_f_type, item)
        sys.exit()

    #  Get pipe steps if any
    pipe_steps = []
    if args.pipe_steps:
        pipe_steps = [PipeStep[p] for p in args.pipe_steps]

    if args.pdf_file:
        #TODO change with run_pipeline()
        bht_run_file(args.pdf_file, papers_dir, BhtFileType.PDF)
    elif args.txt_file:
        if not args.doi:
            print("Set DOI with --doi opt")
            sys.exit()
        if not args.pub_date:
            print("Set Publication_Date with --pub-date opt")
            sys.exit()
        done_steps = run_pipeline(
            doc_meta_info={"doi": args.doi, "pub_date": args.pub_date},
            orig_file=args.txt_file,
            doc_type=BhtFileType.TXT,
            pipe_steps=pipe_steps,
        )
    elif args.pipe_dir:
        if PipeStep.GROBID in pipe_steps and not args.doi:
            print("Include GROBID pipe_step, or use --doi ")
            sys.exit()
        done_steps = run_pipeline(
            doc_meta_info={"doi": args.doi},
            # TODO: pub_date=args.pub_date,
            pipeline_paper_dir=args.pipe_dir,
            orig_file=None,
            doc_type=None,
            pipe_steps=pipe_steps,
        )
    elif args.istex_id:
        # TODO: REFACTOR this could be a "retrieve" step of the pipeline
        # if not args.doi:
        #     print("Set DOI with --doit opt")
        #     sys.exit()
        # doc_type = IstexDoctype.TXT
        doc_type = IstexDoctype.CLEANED
        content, filename, istex_struct = get_file_from_id(args.istex_id, doc_type)
        filepath = os.path.join(yml_settings["BHT_DATA_DIR"], filename)
        with open(filepath, "wb") as binary_file:
            # Write bytes to file
            binary_file.write(content)
        print(f"Written to {filepath}")
        # set default pipeline sequence
        if not pipe_steps:
            pipe_steps = [
                PipeStep.MKDIR,
                PipeStep.FILTER,
                PipeStep.SUTIME,
                PipeStep.ENTITIES,
            ]
        done_steps = run_pipeline(
            doc_meta_info={"doi": istex_struct["doi"]},
            orig_file=filepath,
            doc_type=doc_type,
            pipe_steps=pipe_steps,
        )

    end_time = datetime.now()
    print("TOTAL ELAPSED TIME: ---" + str(end_time - start_time) + "---")
