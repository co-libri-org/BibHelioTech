import os
import shutil

import pytest
import logging
from flask import current_app

from web import create_app
from web import db as _db
from web.models import Paper, HpEvent, BhtFileType, stream_to_db

skip_selenium = pytest.mark.skipif(
    os.environ.get("BHT_SKIP_SELENIUM") is not None
    and os.environ.get("BHT_SKIP_SELENIUM"),
    reason="SELENIUM Skipping",
)

skip_bht = pytest.mark.skipif(
    os.environ.get("BHT_SKIP_BHT") is not None and os.environ.get("BHT_SKIP_BHT"),
    reason="BHT skipping (too long)",
)

skip_istex = pytest.mark.skipif(
    os.environ.get("BHT_SKIP_ISTEX") is not None and os.environ.get("BHT_SKIP_ISTEX"),
    reason="ISTEX skipping (no auth)",
)

skip_slow_test = pytest.mark.skipif(
    os.environ.get("BHT_SKIP_SLOW") is not None and os.environ.get("BHT_SKIP_SLOW"),
    reason="Slow test skipping",
)

# Dont Log WERKZEUG MESSAGES
#
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)


@pytest.fixture(scope="session", autouse=True)
def app():
    """Session-wide flask app."""
    _app = create_app(bht_env="testing")
    _app.config.update(
        # Change the port that the liveserver listens on as we don't want to conflict with running:5000
        LIVESERVER_PORT=8943
    )

    _ctx = _app.app_context()
    _ctx.push()
    #
    yield _app
    #
    _ctx.pop()


@pytest.fixture(scope="function", autouse=True)
def db(app):
    """function-wide test database."""
    # db_file = current_app.config["SQLALCHEMY_DATABASE_URI"].split("sqlite:///")[1]
    # if os.path.exists(db_file):
    #     os.remove(db_file)

    _db.app = app
    _db.create_all()
    #
    yield _db
    #
    _db.session.rollback()
    _db.drop_all()
    _db.session.close()


@pytest.fixture(scope="function")
def paper_with_txt(paper_for_test, txt_for_test):
    """Add a paper's with catalog to db"""
    paper_for_test.set_file_path(txt_for_test, BhtFileType.TXT)
    paper_for_test.set_doi("10.1002/jgra.50537")
    _db.session.add(paper_for_test)
    _db.session.commit()
    #
    yield paper_for_test


@pytest.fixture(scope="function")
def paper_with_cat(paper_for_test, cat_for_test):
    """Add a paper's with catalog to db"""
    paper_for_test.set_cat_path(cat_for_test)
    _db.session.add(paper_for_test)
    _db.session.commit()
    #
    yield paper_for_test


@pytest.fixture(scope="function")
def paper_for_test(pdf_for_test, tmp_path_factory):
    """Add a paper's pdf to db"""
    with open(pdf_for_test, "rb", buffering=0) as fp:
        paper_id = stream_to_db(fp.readall(), os.path.basename(pdf_for_test), tmp_path_factory.mktemp("upload_dir"))
    paper = _db.session.get(Paper, paper_id)
    _db.session.add(paper)
    _db.session.commit()
    #
    yield paper
    # make sure paper exists before deleting
    paper = _db.session.get(Paper, paper_id)
    if paper is not None:
        _db.session.delete(paper)
        _db.session.commit()


@pytest.fixture(scope="module")
def cleaned_for_test():
    test_cleaned_file_orig = os.path.join(
        current_app.config["BHT_RESOURCES_DIR"],
        "CAAEFDA40653763CC8E603A982B2405E1ED646DA.cleaned",
    )
    test_cleaned_file_dest = os.path.join(
        current_app.config["BHT_PAPERS_DIR"],
        "CAAEFDA40653763CC8E603A982B2405E1ED646DA.cleaned",
    )
    shutil.copy(test_cleaned_file_orig, test_cleaned_file_dest)
    #
    yield test_cleaned_file_dest
    #
    if os.path.isfile(test_cleaned_file_dest):
        os.remove(test_cleaned_file_dest)


@pytest.fixture(scope="module")
def txt_for_test():
    test_txt_file_orig = os.path.join(
        current_app.config["BHT_RESOURCES_DIR"], "ark_67375_WNG-SKGBGQ0H-V.txt"
    )
    test_txt_file_dest = os.path.join(
        current_app.config["BHT_PAPERS_DIR"], "ark_67375_WNG-SKGBGQ0H-V.txt"
    )
    shutil.copy(test_txt_file_orig, test_txt_file_dest)
    #
    yield test_txt_file_dest
    #
    if os.path.isfile(test_txt_file_dest):
        os.remove(test_txt_file_dest)


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


@pytest.fixture(scope="module")
def cat_for_test():
    filename = "105194angeo282332010_bibheliotech_V1.txt"
    test_cat_file_orig = os.path.join(
        current_app.config["BHT_RESOURCES_DIR"],
        filename,
    )
    test_cat_file_dest = os.path.join(current_app.config["BHT_PAPERS_DIR"], filename)
    shutil.copy(test_cat_file_orig, test_cat_file_dest)
    #
    yield test_cat_file_dest
    #
    if os.path.isfile(test_cat_file_dest):
        os.remove(test_cat_file_dest)


@pytest.fixture(scope="module")
def big_cat_for_test():
    filename = "big_catalog.txt"
    test_cat_file_orig = os.path.join(
        current_app.config["BHT_RESOURCES_DIR"],
        filename,
    )
    test_cat_file_dest = os.path.join(current_app.config["BHT_PAPERS_DIR"], filename)
    shutil.copy(test_cat_file_orig, test_cat_file_dest)
    #
    yield test_cat_file_dest
    #
    if os.path.isfile(test_cat_file_dest):
        os.remove(test_cat_file_dest)


@pytest.fixture(scope="module")
def small_cat_for_test():
    filename = "small_catalog.txt"
    test_cat_file_orig = os.path.join(
        current_app.config["BHT_RESOURCES_DIR"],
        filename,
    )
    test_cat_file_dest = os.path.join(current_app.config["BHT_PAPERS_DIR"], filename)
    shutil.copy(test_cat_file_orig, test_cat_file_dest)
    #
    yield test_cat_file_dest
    #
    if os.path.isfile(test_cat_file_dest):
        os.remove(test_cat_file_dest)


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
        "stop_date": "2007-07-16T20:18:00.000",
        "doi": "https://doi.org/10.1029/2010JA015404",
        "mission": "THEMIS-A",
        "instrument": "FGM-ESA",
        "region": "Earth.Magnetosheath",
    }
    return hpevent_dict

@pytest.fixture(scope="module")
def hpevent_dict_for_test_new():
    hpevent_dict = {
        "start_time": "2007-07-16T19:50:00.000",
        "stop_time": "2007-07-16T20:18:00.000",
        "doi": "https://doi.org/10.1029/2010JA015404",
        "sats": "THEMIS-A",
        "insts": "FGM-ESA",
        "regs": "Earth.Magnetosheath",
        "conf": 1000
    }
    return hpevent_dict


@pytest.fixture(scope="module")
def catalog_row_6fields():
    catalog_row = [
        "2007-07-16T19:50:00.000",
        "2007-07-16T20:18:00.000",
        "https://doi.org/10.1029/2010JA015404",
        "THEMIS-A",
        "FGM-ESA",
        "Earth.Magnetosheath",
    ]
    return catalog_row
