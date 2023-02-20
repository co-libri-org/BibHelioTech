import os

import pytest

from bht_config import yml_settings
from bht.published_date_finder import published_date_finder
from bht.GROBID_generator import GROBID_generation
from tests.conftest import skip_slow_test, skip_istex
from web import db
from web.errors import IstexParamError
from web.istex_proxy import istex_params_to_json, istex_url_to_json
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

    def test_has_path(self):
        paper = Paper(title="my Paper", pdf_path="/this/is/a/path.pdf")
        assert not paper.has_cat
        assert not paper.has_pdf


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
