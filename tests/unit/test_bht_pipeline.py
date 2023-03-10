from bht_config import yml_settings
from tests.conftest import skip_bht
from web.bht_proxy import pipe_paper


@skip_bht
class TestBhtPipeline:
    def test_pipepaper(self, paper_for_test):
        """
        GIVEN the pipepaper method
        WHEN called
        THEN check paper model changed
        """
        assert not paper_for_test.has_cat
        pipe_paper(paper_for_test.id, yml_settings["BHT_PAPERS_DIR"])
        assert paper_for_test.has_cat
