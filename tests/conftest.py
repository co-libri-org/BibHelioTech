import shutil
from urllib.parse import urlencode

import pytest
import os

from bht_config import yml_settings
from web import create_app, db
from web.config import TestConfig
from web.main.routes import save_to_db
from web.models import Paper

skip_istex = pytest.mark.skipif(
    os.environ.get("BHT_DONTSKIPISTEX") is None
    or not os.environ.get("BHT_DONTSKIPISTEX"),
    reason="ISTEX skipping (no auth)",
)

skip_slow_test = pytest.mark.skipif(
    os.environ.get("BHT_SKIPSLOWTESTS") is not None
    and os.environ.get("BHT_SKIPSLOWTESTS"),
    reason="Slow test skipping",
)


@pytest.fixture(scope="module", autouse=True)
def app():
    app = create_app(TestConfig)

    app_context = app.app_context()
    app_context.push()
    db.create_all()

    yield app

    # clean up / reset resources here


@pytest.fixture(scope="module")
def tei_for_test():
    test_tei_file = os.path.join(yml_settings["BHT_PAPERS_DIR"], "2016GL069787.tei.xml")
    yield test_tei_file
    if os.path.isfile(test_tei_file):
        os.remove(test_tei_file)


@pytest.fixture(scope="module")
def pdf_for_test():
    test_pdf_file_orig = os.path.join(
        yml_settings["BHT_RESOURCES_DIR"], "2016GL069787-test.pdf"
    )
    test_pdf_file_dest = os.path.join(
        yml_settings["BHT_PAPERS_DIR"], "2016GL069787-test.pdf"
    )
    shutil.copy(test_pdf_file_orig, test_pdf_file_dest)

    yield test_pdf_file_dest

    if os.path.isfile(test_pdf_file_dest):
        os.remove(test_pdf_file_dest)


@pytest.fixture(scope="function")
def paper_for_test(pdf_for_test):
    with open(pdf_for_test, "rb", buffering=0) as fp:
        paper_id = save_to_db(fp.readall(), os.path.basename(pdf_for_test))
    paper = db.session.get(Paper, paper_id)
    yield paper
    # make sure paper exists before deleting
    paper = db.session.get(Paper, paper_id)
    if paper is not None:
        db.session.delete(paper)
        db.session.commit()


@pytest.fixture(scope="module")
def test_client(app):
    yield app.test_client()


@pytest.fixture(scope="module")
def istex_params():
    _publication_date = "[2020 *]"
    _abstract = "solar AND wind"
    _params = {
        "q": f"(publicationDate:{_publication_date} AND abstract:({_abstract}))",
        "facet": "corpusName[*]",
        "size": 150,
        "output": "*",
        "stats": "",
    }
    yield _params


@pytest.fixture(scope="module")
def istex_url():
    _publication_date = "[2020 *]"
    _abstract = "solar AND wind"
    _params = {
        "q": f"(publicationDate:{_publication_date} AND abstract:({_abstract}))",
        "facet": "corpusName[*]",
        "size": 150,
        "output": "*",
        "stats": "",
    }
    yield "https://api.istex.fr/document/?" + urlencode(_params)


@pytest.fixture(scope="module")
def istex_id():
    yield "BA3BC0C1E5A6B64AD5CBDE9C29AC2611455EE9A1"
