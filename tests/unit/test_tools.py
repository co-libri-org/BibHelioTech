from web.cat_tools import catfile_to_rows


class TestCatTools:
    def test_read_cat_read(self, cat_for_test):
        hp_events = catfile_to_rows(cat_for_test)
        assert len(hp_events) == 46
