from pprint import pprint

from web.bht_proxy import get_pipe_callback, pipe_paper_mocked
from web.istex_proxy import istex_url_to_json


class TestBhtIstex:
    def test_url_to_json(self, istex_url):
        istex_list = istex_url_to_json(istex_url)
        pprint(istex_list)
        assert len(istex_list) == 150
        assert "title" in istex_list[0]
        assert "pdf_url" in istex_list[0]
        assert "abstract" in istex_list[0]

    def test_txt_in_json(self, istex_url):
        istex_list = istex_url_to_json(istex_url)
        assert "txt_url" in istex_list[0]


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

    def test_pipepaper_mocked(self):
        """
        GIVEN the mocking pipepaper method
        WHEN called
        THEN check it slept
        """
        max_secs = 2
        slept = pipe_paper_mocked(min_secs=1, max_secs=max_secs)
        assert slept <= max_secs
