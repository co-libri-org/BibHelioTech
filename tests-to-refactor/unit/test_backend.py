import os

from bht_config import yml_settings
from bht.published_date_finder import published_date_finder
from bht.GROBID_generator import GROBID_generation
from tests.conftest import skip_slow_test


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
