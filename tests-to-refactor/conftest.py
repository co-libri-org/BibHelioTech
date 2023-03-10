import pytest

from web import db


@pytest.fixture(scope="function")
def hpevents_in_db(hpevents_list):
    for event in hpevents_list:
        db.session.add(event)
        db.session.commit
