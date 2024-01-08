from web.bht_proxy import get_pipe_callback, pipe_paper_mocked, pipe_paper
from web.istex_proxy import json_to_hits


class TestBhtIstex:
    def test_txt_in_json(self, istex_search_json):
        istex_list = json_to_hits(istex_search_json)
        assert "txt" in istex_list[0]["doc_urls"]


class TestBhtProxy:
    def test_get_pipe_callback(self):
        """
        GIVEN the get_pipe_callback method
        WHEN called with boolean
        THEN check it returns appropriate method
        """
        notest_callback = get_pipe_callback(test=False)
        test_callback = get_pipe_callback(test=True)
        assert test_callback.__name__ == "pipe_paper_mocked"
        assert notest_callback.__name__ == "pipe_paper"

    def test_pipe_paper_mocked(self):
        """
        GIVEN the mocking pipepaper method
        WHEN called
        THEN check it slept
        """
        max_secs = 2
        slept = pipe_paper_mocked(min_secs=1, max_secs=max_secs)
        assert slept <= max_secs

    def test_pipe_paper(self, paper_with_txt, tmp_path):
        """
        GIVEN the pipepaper method
        WHEN called
        THEN check it slept
        """
        _paper_id = paper_with_txt.id
        assert not paper_with_txt.has_cat
        _res_paper_id = pipe_paper(_paper_id, tmp_path, "txt")
        assert _paper_id == _res_paper_id
        assert paper_with_txt.has_cat
