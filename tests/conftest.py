import shutil
from urllib.parse import urlencode

import pytest
import os

from flask import current_app

from web import create_app, db
from web.main.routes import save_to_db
from web.models import Paper, HpEvent

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


@pytest.fixture(scope="session", autouse=True)
def app():
    app = create_app(bht_env="testing")
    app.config.update(
        # Change the port that the liveserver listens on as we don't want to conflict with running:5000
        LIVESERVER_PORT=8943
    )

    app_context = app.app_context()
    app_context.push()
    db.create_all()

    yield app

    # clean up / reset resources here


@pytest.fixture(scope="module")
def tei_for_test():
    test_tei_file = os.path.join(
        current_app.config["BHT_PAPERS_DIR"], "2016GL069787.tei.xml"
    )
    yield test_tei_file
    if os.path.isfile(test_tei_file):
        os.remove(test_tei_file)


@pytest.fixture(scope="module")
def hpevents_list():
    hpevents_list = [
        HpEvent(
            "2007-07-16T19:50:00.000",
            "2007-07-16T20:37:00.000",
            "doiA",
            "missionA",
            "instrumentA",
            "regionA",
        ),
        HpEvent(
            "2007-07-16T19:50:00.000",
            "2007-07-16T20:37:00.000",
            "doiB",
            "missionB",
            "instrumentB",
            "regionB",
        ),
        HpEvent(
            "2007-07-16T19:50:00.000",
            "2007-07-16T20:37:00.000",
            "doiC",
            "missionC",
            "instrumentC",
            "regionC",
        ),
    ]
    return hpevents_list


@pytest.fixture(scope="module")
def hpevent_dict_for_test():
    hpevent_dict = {
        "start_date": "2007-07-16T19:50:00.000",
        "stop_date": "2007-07-16T20:00:00.000",
        "doi": "https://doi.org/10.1029/2010JA015404",
        "mission": "THEMIS-A",
        "instrument": "FGM-ESA",
        "region": "Earth.Magnetosheath",
    }
    return hpevent_dict


@pytest.fixture(scope="module")
def cat_for_test():
    test_cat_file_orig = os.path.join(
        current_app.config["BHT_RESOURCES_DIR"],
        "105194angeo282332010_bibheliotech_V1.txt",
    )
    yield test_cat_file_orig


@pytest.fixture(scope="module")
def pdf_for_test():
    test_pdf_file_orig = os.path.join(
        current_app.config["BHT_RESOURCES_DIR"], "2016GL069787-test.pdf"
    )
    test_pdf_file_dest = os.path.join(
        current_app.config["BHT_PAPERS_DIR"], "2016GL069787-test.pdf"
    )
    shutil.copy(test_pdf_file_orig, test_pdf_file_dest)
    #
    yield test_pdf_file_dest
    #
    if os.path.isfile(test_pdf_file_dest):
        os.remove(test_pdf_file_dest)


@pytest.fixture(scope="function")
def paper_for_test(pdf_for_test):
    """Adds a paper's pdf to db"""
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
