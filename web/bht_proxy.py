from bht.__main__ import run_file as bht_run_file
from web.models import Paper


def runfile_and_updatedb(paper_id, pdf_file, basedir):
    catalogfile = bht_run_file(pdf_file, basedir)
    paper = Paper.query.get(paper_id)
    paper.set_cat_path(catalogfile)
