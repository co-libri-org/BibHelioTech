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
    TIMEFILL = auto()
    ENTITIES = auto()


_logger = init_logger()


# TODO: REWRITE IstexDocType or BhtFileType ??
def run_step_mkdir(orig_file: str, pipeline_root_dir: str, doc_type: IstexDoctype) -> str:
    """
    Move a pdf or txt file to same name directory

    @param doc_type:
    @param orig_file:
    @param pipeline_root_dir:
    @return:
    """
    # 0- Move original file to working directory
    _logger.info("BHT PIPELINE STEP 0: creating file directory")
    if doc_type not in [IstexDoctype.PDF, IstexDoctype.TXT, IstexDoctype.CLEANED]:
        raise (BhtPipelineError(f"Such doctype not managed {doc_type}"))
    filename = os.path.basename(orig_file)
    split_filename = os.path.splitext(filename)
    dest_dir = os.path.join(pipeline_root_dir, split_filename[0])
    if doc_type == IstexDoctype.PDF:
        dest_file = os.path.join(dest_dir, filename)
    elif doc_type in [IstexDoctype.TXT, IstexDoctype.CLEANED]:
        dest_file = os.path.join(dest_dir, "out_text.txt")
    else:
        raise BhtPipelineError("Wrong IstexDoctype")
    os.makedirs(dest_dir, exist_ok=True)
    shutil.copy(orig_file, dest_file)
    return dest_dir


def run_step_ocr(dest_pdf_dir):
    # 1- OCR the pdf file
    _logger.info("BHT PIPELINE STEP 1: Ocerising pdf")
    search_pattern = os.path.join(dest_pdf_dir, "*.pdf")
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
    from sutime import SUTime
    from bht.SUTime_processing import SUTime_treatement

    sutime = SUTime(mark_time_ranges=True, include_range=True)  # load sutime wrapper
    # SUTime read all the file and save its results in a file "res_sutime.json"
    SUTime_treatement(dest_pdf_dir, sutime)


def run_step_timefill(dest_pdf_dir):
    """" from a sutime json  transform date and create a json_2 """
    _logger.info("BHT PIPELINE STEP 5: TimeTransform")
    from bht.SUTime_processing import SUTime_transform

    # transforms some results of sutime to complete missing, etc ... save results in "res_sutime_2.json"
    SUTime_transform(dest_pdf_dir)


def run_step_entities(dest_pdf_dir, doc_meta_info=None):
    _logger.info("BHT PIPELINE STEP 6: Search Entities")
    catalog_file = entities_finder(dest_pdf_dir, doc_meta_info)
    return catalog_file

def bht_run_file(orig_file, result_base_dir, file_type, doc_meta_info=None):
    """
    Given a file of type <file_type>, go through the whole pipeline process and make a catalog

    @param file_type: either pdf or txt or any of BhtFileType
    @param orig_file: the sci article in pdf or txt format
    @param result_base_dir: the root working directory
    @param doc_meta_info: dict with paper doi, istex_id, publication_date ...
    @return: an HPEvents catalog
    """
    # Set default steps
    steps = [
        PipeStep.MKDIR,
        PipeStep.FILTER,
        PipeStep.SUTIME,
        PipeStep.TIMEFILL,
        PipeStep.ENTITIES
    ]

    # Add 2 more steps for PDF file
    if file_type == BhtFileType.PDF:
        # steps = [PipeStep.MKDIR, PipeStep.OCR, PipeStep.GROBID] + steps[1:]
        steps.insert(1, PipeStep.OCR)
        steps.insert(2, PipeStep.GROBID)

    # Run pipeline, and get catalog file
    output_container = {}
    done_steps = run_pipeline(
        orig_file=orig_file,
        doc_type=file_type,
        pipe_steps=steps,
        dest_file_dir=result_base_dir,
        doc_meta_info=doc_meta_info,
        output_container=output_container
    )

    # Vérification du fichier de catalogue
    catalog_file = output_container.get("catalog_file")
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
                ".pdf"
        ):  # If '.pdf' on "Papers" folder --> paper not treated --> processing paper treatment.
            # create the directory under the same name as the paper.
            os.makedirs(os.path.join(_base_pdf_dir, folders_or_pdf.replace(".pdf", "")))
            # move '.pdf' to his directory.
            shutil.move(
                folders_or_pdf_path,
                os.path.join(_base_pdf_dir, folders_or_pdf.replace(".pdf", "")),
            )
        pdf_paths = os.path.join(_base_pdf_dir, folders_or_pdf.replace(".pdf", ""))
        from sutime import SUTime
        from bht.SUTime_processing import SUTime_treatement, SUTime_transform

        sutime = SUTime(
            mark_time_ranges=True, include_range=True
        )  # load sutime wrapper
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
                    entities_finder(
                        pdf_paths
                    )  # entities recognition and association + writing of HPEvent


def run_pipeline(orig_file, doc_type, pipe_steps=(), pipeline_root_dir=None, dest_file_dir=None, doc_meta_info=None,
                 output_container=None):
    """


    @param orig_file: original scientifique article (txt or pdf file)
    @param doc_type: is it a txt or pdf file
    @param pipe_steps: pipeline steps to run
    @param pipeline_root_dir: root directory where to make subdirectory for this pipeline
    @param dest_file_dir: pipeline output directory in case of steps after step_mkdir
    @param doc_meta_info:  contains doi and pub_date
    @param output_container: dictionnary to store alternate return values ("catalog_file" key for ex.)
    @return: done_steps
    """
    done_steps = []
    # Choose all steps if none or empty
    if not pipe_steps:
        pipe_steps = list(PipeStep)
    # Check type
    for s in pipe_steps:
        if not isinstance(s, PipeStep):
            raise (BhtPipelineError(f"No such step >>>> {s} <<<<<"))

    if PipeStep.MKDIR in pipe_steps:
        pipeline_root_dir = pipeline_root_dir or yml_settings["BHT_DATA_DIR"]
        dest_file_dir = run_step_mkdir(
            orig_file, pipeline_root_dir, doc_type=doc_type
        )
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

    if PipeStep.TIMEFILL in pipe_steps:
        run_step_timefill(dest_file_dir)
        done_steps.append(PipeStep.TIMEFILL)

    if PipeStep.ENTITIES in pipe_steps:
        catalog_file = run_step_entities(dest_file_dir, doc_meta_info)
        # Store catalog_file in the result container, if provided
        if output_container is not None:
            output_container["catalog_file"] = catalog_file
        done_steps.append(PipeStep.ENTITIES)

    return done_steps
