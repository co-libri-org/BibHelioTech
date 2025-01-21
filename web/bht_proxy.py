import os.path

from bht.errors import BhtPathError
from bht.pipeline import bht_run_file
from web import db
from web.errors import *
from web.models import Paper, BhtFileType


def random_sleep(min_secs, max_secs):
    import time
    import random

    num_secs = random.randint(min_secs, max_secs)
    time.sleep(num_secs)
    return num_secs


def get_pipe_callback(test=True, fail=False):
    """Wrapper to exec a task callback depending on configuration

    @return: callback
    """

    if fail:
        return pipe_paper_failed
    if test:
        return pipe_paper_mocked
    else:
        return pipe_paper


def pipe_paper_failed(_p_id, _b_dir, _ft):
    """Raise exception after a random num of seconds"""
    num_secs = random_sleep(min_secs=5, max_secs=20)
    raise WebError(f"Failed after {num_secs} seconds")


def pipe_paper_mocked(p_id=None, b_dir=None, file_type=None, min_secs=5, max_secs=20):
    """Spend time a random num of seconds

    @return: num seconds spent
    """
    return random_sleep(min_secs, max_secs)


# TODO: REFACTOR should this go to a models.paper.method() ?
def pipe_paper(paper_id, basedir=None, file_type=None):
    """From a paper id create the catalog

    - find the corresponding cleaned (or pdf) file
    - pass it to the bht pipeline
    - store the resulting catalog
    - update db

    """
    _paper = db.session.get(Paper, paper_id)
    # Set pipeline defaults if it has txt file only
    if basedir is None or file_type is None:
        if not _paper.has_txt:
            raise BhtPathError("Set pipeline defaults only if paper has txt file ")
    if basedir is None:
        basedir = os.path.dirname(_paper.txt_path)
    if file_type is None:
        file_type = BhtFileType.TXT

    # TODO: REFACTOR better call models.paper.get_file()
    if file_type == BhtFileType.PDF and _paper.has_pdf:
        file_path = _paper.pdf_path
    elif file_type == BhtFileType.TXT and _paper.has_txt:
        file_path = _paper.txt_path
    else:
        raise FilePathError(
            f"No such file for paper {paper_id} \n"
            f"pdf: {_paper.pdf_path}"
            f"txt: {_paper.txt_path}"
            f"and type {file_type}: hastxt={_paper.has_txt} haspdf={_paper.has_pdf}"
        )
    _doc_meta_info = {"doi": _paper.doi, "pub_date": _paper.publication_date}
    catalogfile = bht_run_file(file_path, basedir, file_type, _doc_meta_info)
    # cat_in_db= _paper.cat_in_db
    _paper.set_cat_path(catalogfile)
    # if cat_in_db:
    #     _paper.push_cat(force=True)
    # TODO: return real result
    return _paper.id
