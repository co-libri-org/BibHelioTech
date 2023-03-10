import pytest
import os

from flask import current_app

from web import db


@pytest.fixture(scope="function", autouse=True)
def fresh_db():
    # db_file = current_app.config["SQLALCHEMY_DATABASE_URI"].split("sqlite:///")[1]
    # if os.path.exists(db_file):
    #     os.remove(db_file)
    # yield db
    # db.session.rollback()
    # db.session.drop_all()
    # db.session.close()
    pass


@pytest.fixture(scope="module")
def tei_for_test():
    test_tei_file = os.path.join(
        current_app.config["BHT_PAPERS_DIR"], "2016GL069787.tei.xml"
    )
    yield test_tei_file
    if os.path.isfile(test_tei_file):
        os.remove(test_tei_file)


@pytest.fixture(scope="function")
def hpevents_in_db(hpevents_list):
    for event in hpevents_list:
        db.session.add(event)
        db.session.commit


@pytest.fixture(scope="module")
def test_client(app):
    yield app.test_client()
