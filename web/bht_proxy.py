from bht.pipeline import bht_run_file
from web import db
from web.errors import PdfFileError
from web.models import Paper, BhtFileType


def get_pipe_callback(test=True):
    """Wrapper to exec a task callback depending on configuration

    @return: callback
    """

    if test:
        return pipe_paper_mocked
    else:
        return pipe_paper


def pipe_paper_mocked(p_id=None, b_dir=None, file_type=None, min_secs=5, max_secs=20):
    """Spend time

    @return: num seconds spent
    """
    import time
    import random

    num_secs = random.randint(min_secs, max_secs)
    time.sleep(num_secs)
    return num_secs


# TODO: REFACTOR should this go to a models.paper.method() ?
def pipe_paper(paper_id, basedir, file_type):
    """From a paper id create the catalog

    - find the corresponding pdf file
    - pass it to the bht pipeline
    - store the resulting catalog
    - update db

    """
    _paper = db.session.get(Paper, paper_id)
    # TODO: REFACTOR better call models.paper.get_file()
    if file_type == BhtFileType.PDF and _paper.has_pdf:
        file_path = _paper.pdf_path
    elif file_type == BhtFileType.TXT and _paper.has_txt:
        file_path = _paper.txt_path
    else:
        raise PdfFileError(f"No such file for paper{paper_id}")
    catalogfile = bht_run_file(file_path, basedir, file_type)
    _paper.set_cat_path(catalogfile)
    # FIXME: return real result
    return "Paper Piped"
