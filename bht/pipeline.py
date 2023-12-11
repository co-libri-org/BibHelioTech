import glob
import os
import shutil
from enum import IntEnum, auto

from bht.Entities_finder import entities_finder
from bht.GROBID_generator import GROBID_generation
from bht.OCR_filtering import ocr_filter
from bht.OCRiser import PDF_OCRiser
from bht.bht_logging import init_logger
from bht.errors import BhtResultError, BhtPipelineError
from bht_config import yml_settings
from web.istex_proxy import IstexDoctype
from web.models import BhtFileType


class PipeStep(IntEnum):
    MKDIR = auto()
    OCR = auto()
    GROBID = auto()
    FILTER = auto()
    SUTIME = auto()
    ENTITIES = auto()


_logger = init_logger()


# TODO: hey, doc_type looks like file_type: IstexDocType or BhtFileType ??
def run_step_mkdir(orig_file, result_base_dir, doc_type):
    """
    Move a pdf file to same name directory

    @param doc_type:
    @param orig_file:
    @param result_base_dir:
    @return:
    """
    # 0- Move original file to working directory
    _logger.info("BHT PIPELINE STEP 0: creating file directory")
    if doc_type not in [IstexDoctype.PDF, IstexDoctype.TXT]:
        raise (BhtPipelineError(f"Such doctype not managed {doc_type}"))
    filename = os.path.basename(orig_file)
    split_filename = os.path.splitext(filename)
    dest_dir = os.path.join(result_base_dir, split_filename[0])
    if doc_type == IstexDoctype.PDF:
        dest_file = os.path.join(dest_dir, filename)
    elif doc_type == IstexDoctype.TXT:
        dest_file = os.path.join(dest_dir, 'out_text.txt')
    else:
        raise BhtPipelineError("Wrong IstexDoctype")
    os.makedirs(dest_dir, exist_ok=True)
    shutil.copy(orig_file, dest_file)
    return dest_dir


def run_step_ocr(dest_pdf_dir):
    # 1- OCR the pdf file
    _logger.info("BHT PIPELINE STEP 1: Ocerising pdf")
    search_pattern = os.path.join(dest_pdf_dir, '*.pdf')
    dest_pdf_file = glob.glob(search_pattern, recursive=True)[0]
    PDF_OCRiser(dest_pdf_dir, dest_pdf_file)


def run_step_grobid(dest_pdf_dir):
    _logger.info("BHT PIPELINE STEP 2: Grobidding")
    GROBID_generation(dest_pdf_dir)


def run_step_filter(dest_pdf_dir):
    _logger.info("BHT PIPELINE STEP 3: Filtering")
    ocr_filter(dest_pdf_dir)


def run_step_sutime(dest_pdf_dir):
    _logger.info("BHT PIPELINE STEP 4: Sutime")
    from bht.SUTime_processing import SUTime, SUTime_treatement, SUTime_transform

    sutime = SUTime(mark_time_ranges=True, include_range=True)  # load sutime wrapper
    # SUTime read all the file and save its results in a file "res_sutime.json"
    SUTime_treatement(dest_pdf_dir, sutime)
    # transforms some results of sutime to complete missing, etc ... save results in "res_sutime_2.json"
    SUTime_transform(dest_pdf_dir)


def run_step_entities(dest_pdf_dir, doi=None):
    _logger.info("BHT PIPELINE STEP 5: Search Entities")
    entities_finder(dest_pdf_dir, doi)
    search_pattern = os.path.join(dest_pdf_dir, '**', '*bibheliotech*.txt')
    _logger.debug(f"searching {search_pattern}")
    result_catalogs = glob.glob(search_pattern, recursive=True)
    catalog_file = result_catalogs[0]
    return catalog_file


def bht_run_file(orig_pdf_file, result_base_dir, file_type, doi=None):
    """
    Given a pdf file , go through the whole pipeline process and make a cataog

    @param file_type:
    @param orig_pdf_file:  the sci article in pdf format
    @param result_base_dir: the root working directory
    @return: an HPEvents catalog
    """

    # 0
    dest_pdf_dir = run_step_mkdir(orig_pdf_file, result_base_dir, file_type)

    # TODO: instead run a run_pipeline() with proper parameters
    if file_type == BhtFileType.PDF:
        # 1
        run_step_ocr(dest_pdf_dir)

        # 2- Generate the XML GROBID file
        run_step_grobid(dest_pdf_dir)

    # 3- filter result of the OCR to deletes references, change HHmm4 to HH:mm, etc ...
    run_step_filter(dest_pdf_dir)

    # 3- Sutime processing
    run_step_sutime(dest_pdf_dir)

    # 4- Entities recognition, association and writing of HPEvent
    catalog_file = run_step_entities(dest_pdf_dir, doi)

    if not os.path.isfile(catalog_file):
        raise BhtResultError(f"No such file {catalog_file}")
    return catalog_file


def bht_run_dir(_base_pdf_dir):
    """
    Given a base directory, operate all the  pipeline operations

    @param _base_pdf_dir:
    @return:  None
    """
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


def run_pipeline(path, doc_type, pipe_steps=(), dest_file_dir=None):
    """

    @param dest_file_dir:
    @param doc_type:
    @param path:
    @param pipe_steps:
    @return:
    """
    done_steps = []
    for s in pipe_steps:
        if not isinstance(s, PipeStep):
            raise (BhtPipelineError("So such step"))

    if PipeStep.MKDIR in pipe_steps:
        dest_file_dir = run_step_mkdir(path, yml_settings["BHT_DATA_DIR"], doc_type=doc_type)
        done_steps.append(PipeStep.MKDIR)

    if PipeStep.OCR in pipe_steps:
        run_step_ocr(dest_file_dir)
        done_steps.append(PipeStep.OCR)

    if PipeStep.GROBID in pipe_steps:
        run_step_grobid(dest_file_dir)
        done_steps.append(PipeStep.GROBID)

    if PipeStep.FILTER in pipe_steps:
        run_step_filter(dest_file_dir)
        done_steps.append(PipeStep.FILTER)

    if PipeStep.SUTIME in pipe_steps:
        run_step_sutime(dest_file_dir)
        done_steps.append(PipeStep.SUTIME)

    if PipeStep.ENTITIES in pipe_steps:
        run_step_entities(dest_file_dir)
        done_steps.append(PipeStep.ENTITIES)

    return done_steps
