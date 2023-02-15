import os

import pytest

from bht_config import yml_settings
from bht.published_date_finder import published_date_finder
from bht.GROBID_generator import GROBID_generation
from tests.conftest import skip_slow_test
from web import db
from web.errors import IstexParamError
from web.istex_proxy import istex_params_to_json
from web.models import Paper


class TestDb:
    def test_db_created(self):
        """
        GIVEN a Flask app (see autouse fixture in conftest.py )
        WHEN db session is used for saving an object
        THEN check that the object was saved
        """
        my_path = "/paper/path/to.pdf"
        my_title = "Paper Title"
        paper = Paper(title=my_title, pdf_path=my_path)
        db.session.add(paper)
        db.session.commit()
        found_paper = Paper.query.filter_by(title=my_title).one()
        assert found_paper.pdf_path == my_path


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


class TestIstex:
    def test_params_to_json_missing_key(self):
        with pytest.raises(IstexParamError):
            istex_params_to_json({"key": "value"})

    def test_params_to_json(self, istex_request):
        pass
        # assert 'hits' in r.json()
