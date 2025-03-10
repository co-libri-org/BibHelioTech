import glob
import os

import pytest
from flask import current_app

from selenium import webdriver

from web.models import file_to_db


@pytest.fixture(scope="module")
def firefox_driver():
    from selenium.webdriver.firefox.options import Options
    from subprocess import getoutput

    options = Options()
    # options.add_argument("--headless")
    options.binary_location = getoutput("find /snap/firefox -name firefox").split("\n")[
        -1
    ]
    driver = webdriver.Firefox(options=options)
    yield driver


@pytest.fixture(scope="function")
def paperslist_for_tests(tmp_path_factory, db):
    """Add to db a list of pdf papers found in DATA/Papers-dist/ dir

    :return: list of papers id from db
    """
    papers_ids = []
    papers_dir = os.path.join(current_app.config["BHT_DATA_DIR"], "Papers-dist")
    pdf_list = glob.glob(
        os.path.join(papers_dir, "**", "angeo*pdf"),
        recursive=True,
    )
    for pdf_file in pdf_list:
        with open(pdf_file, "rb", buffering=0) as fp:
            _id = file_to_db(fp.read(), os.path.basename(pdf_file), tmp_path_factory.mktemp("upload_dir"))
            papers_ids.append(_id)
    yield papers_ids
