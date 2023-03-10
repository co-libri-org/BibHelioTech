import pytest

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


@pytest.fixture(scope="function")
def hpevents_in_db(hpevents_list):
    for event in hpevents_list:
        db.session.add(event)
        db.session.commit


@pytest.fixture(scope="module")
def test_client(app):
    yield app.test_client()
