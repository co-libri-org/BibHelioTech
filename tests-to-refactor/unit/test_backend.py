import os

import pytest

from bht_config import yml_settings
from bht.published_date_finder import published_date_finder
from bht.GROBID_generator import GROBID_generation
from tests.conftest import skip_slow_test, skip_istex
from web.bht_proxy import pipe_paper, pipe_paper_mocked, get_pipe_callback
from web.errors import IstexParamError
from web.istex_proxy import istex_params_to_json, istex_url_to_json, istex_id_to_url


class TestAds:
    def test_published_date(self):
        from sys import version

        token = "IXMbiJNANWTlkMSb4ea7Y5qJIGCFqki6IJPZjc1m"  # API Key
        doi = "10.1002/2016gl069787"
        found_date = published_date_finder(token, version, doi)
        assert "2017-04-01T00:00:00Z" == found_date


class TestGrobid:
    @skip_slow_test
    def test_grobid_generation(self, tei_for_test):
        GROBID_generation(
            yml_settings["BHT_PAPERS_DIR"]
        )  # generate the XML GROBID file
        assert os.path.isfile(tei_for_test)


class TestRq:
    def test_bht_status(self):
        pass


class TestBhtProxy:
    def test_get_pipe_callback(self):
        notest_callback = get_pipe_callback(test=False)
        test_callback = get_pipe_callback(test=True)
        assert test_callback.__name__ == "pipe_paper_mocked"
        assert notest_callback.__name__ == "pipe_paper"

    def test_pipepaper_mocked(self):
        max_secs = 10
        slept = pipe_paper_mocked(min_secs=1, max_secs=max_secs)
        assert slept <= max_secs
        pass

    def test_pipepaper(self, paper_for_test):
        assert not paper_for_test.has_cat
        pipe_paper(paper_for_test.id, yml_settings["BHT_PAPERS_DIR"])
        assert paper_for_test.has_cat


@skip_istex
class TestIstex:
    def test_params_to_json_missing_key(self):
        with pytest.raises(IstexParamError):
            istex_params_to_json({"key": "value"})

    @skip_slow_test
    def test_params_to_json(self, istex_params):
        istex_list = istex_params_to_json(istex_params)
        assert len(istex_list) == 150
        assert "title" in istex_list[0]
        assert "first_author" in istex_list[0]
        assert "journal" in istex_list[0]
        assert "year" in istex_list[0]
        assert "abstract" in istex_list[0]
        assert "pdf_url" in istex_list[0]

    def test_url_to_json(self, istex_url):
        istex_list = istex_url_to_json(istex_url)
        assert len(istex_list) == 150
        assert "title" in istex_list[0]
        assert "abstract" in istex_list[0]

    def test_id_to_url(self, istex_id):
        istex_url = istex_id_to_url(istex_id)
        assert istex_id in istex_url
