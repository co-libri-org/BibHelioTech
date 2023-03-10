from web import db
from web.models import catfile_to_rows, catfile_to_db, rows_to_catstring
from web.models import HpEvent


# TODO: move to TestModels


class TestCatTools:
    def test_catfile_to_rows(self, cat_for_test):
        hp_events = catfile_to_rows(cat_for_test)
        assert len(hp_events) == 46

    def test_catfile_to_db(self, cat_for_test):
        catfile_to_db(cat_for_test)
        allevents = db.session.query(HpEvent).all()
        assert len(allevents) == 46

    def test_rows_to_catstring(self, cat_for_test):
        hp_events = catfile_to_rows(cat_for_test)
        cat_str = rows_to_catstring(hp_events, "what")
        assert len(cat_str) == 6900
