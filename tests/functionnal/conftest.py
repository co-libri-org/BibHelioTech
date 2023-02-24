import glob
import os

import pytest
from flask import current_app
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from web.main.routes import save_to_db


@pytest.fixture(scope="module")
def firefox_driver():
    options = Options()
    options.add_argument("-headless")
    driver = webdriver.Firefox(options=options)
    yield driver


@pytest.fixture(scope="session", autouse=True)
def paperslist_for_tests():
    papers_ids = []
    papers_dir = os.path.join(current_app.config["BHT_DATA_DIR"], "Papers-dist")
    pdf_list = glob.glob(
        os.path.join(papers_dir, "**", "angeo*pdf"),
        recursive=True,
    )
    for pdf_file in pdf_list:
        with open(pdf_file, "rb", buffering=0) as fp:
            papers_ids.append(save_to_db(fp.readall(), os.path.basename(pdf_file)))
    yield papers_ids
