import pytest
from web import db


@pytest.fixture(scope="function", autouse=True)
def fresh_db():
    db.create_all()
    yield db
    db.session.rollback()
