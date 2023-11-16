from bht.pipeline import bht_run_file
from web import db
from web.errors import PdfFileError
from web.models import Paper


def get_pipe_callback(test=True):
    """Wrapper to exec a task callback depending on configuration

    @return: callback
    """

    if test:
        return pipe_paper_mocked
    else:
        return pipe_paper


def pipe_paper_mocked(p_id=None, b_dir=None, min_secs=5, max_secs=20):
    """Spend time

    @return: num seconds spent
    """
    import time
    import random

    num_secs = random.randint(min_secs, max_secs)
    time.sleep(num_secs)
    return num_secs


def pipe_paper(paper_id, basedir):
    """From a paper id create the catalog

    - find the corresponding pdf file
    - pass it to the bht pipeline
    - store the resulting catalog
    - update db

    """
    _paper = db.session.get(Paper, paper_id)
    if not _paper.has_pdf:
        raise PdfFileError(f"No such file for paper{paper_id}")
    pdf_file = _paper.pdf_path
    catalogfile = bht_run_file(pdf_file, basedir)
    _paper.set_cat_path(catalogfile)
