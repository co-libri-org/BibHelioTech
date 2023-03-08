import os

import pytest

from bht_config import yml_settings
from bht.published_date_finder import published_date_finder
from bht.GROBID_generator import GROBID_generation
from tests.conftest import skip_slow_test, skip_istex
from web import db
from web.bht_proxy import pipe_paper, pipe_paper_mocked, get_pipe_callback
from web.errors import IstexParamError
from web.istex_proxy import istex_params_to_json, istex_url_to_json, istex_id_to_url
from web.models import Paper, Doi, Mission, Instrument, Region, HpEvent, Catalog


class TestModels:
    def test_paper(self):
        """
        GIVEN Paper model
        WHEN class is instantiated
        THEN verify existence
        """
        paper = Paper(title="title", pdf_path="path")
        assert paper.title == "title"
        assert paper.pdf_path == "path"

    def test_paper_cat_in_db(self):
        """
        GIVEN Paper model
        WHEN class is instantiated
        THEN verify catalog not in db first
        """
        paper = Paper(title="title", pdf_path="path")
        assert not paper.cat_in_db

    def test_paper_push_cat(self, paper_for_test):
        """
        GIVEN Paper model instantiated
        WHEN push_cat() is called
        THEN verify attr is changed, ad db was populated
        """
        assert not paper_for_test.cat_in_db
        paper_for_test.push_cat()
        assert paper_for_test.cat_in_db

    def test_catalog(self, hpevents_list):
        """
        GIVEN HpEvent List and Catalog Model
        WHEN events are added to catalog
        THEN verify existence and integrity
        """
        c = Catalog()
        db.session.add(c)
        for event in hpevents_list:
            db.session.add(event)
            c.hp_events.append(event)
            db.session.commit
        # TODO: where assert is ?
        assert False

    def test_hpevent_from_dict(self, hpevent_dict_for_test):
        """
        GIVEN a hp_event dict
        WHEN create hpevent instance
        THEN verify integrity
        """
        hpevent = HpEvent(**hpevent_dict_for_test)
        assert hpevent.doi.doi == hpevent_dict_for_test["doi"]

    def test_hpevent_constructor(self):
        """
        GIVEN HpEvent model
        WHEN class is instantiated and db added
        THEN verify integrity
        """
        hp_event_in = HpEvent(
            "2007-07-16T19:50:00.000",
            "2007-07-16T20:37:00.000",
            "doi",
            "mission",
            "instrument",
            "region",
        )
        db.session.add(hp_event_in)
        db.session.commit()
        hp_event_out = db.session.query(HpEvent).one()
        import datetime

        assert type(hp_event_out.start_date) is datetime.date
        assert hp_event_out.doi.doi == "doi"
        assert hp_event_out.mission.name == "mission"
        assert hp_event_out.instrument.name == "instrument"
        assert hp_event_out.region.name == "region"

    def test_hpevent_get_dict(self, hpevent_dict_for_test):
        """
        GIVEN an hpevent dict
        WHEN HpEvent is created with that dict
        THEN verify output dict is the same
        """
        hpevent_in = HpEvent(**hpevent_dict_for_test)
        dict_out = hpevent_in.get_dict()
        assert hpevent_dict_for_test == dict_out

    def test_doi(self):
        """
        GIVEN Doi model
        WHEN class is instantiated
        THEN verify existence
        """
        doi = Doi(doi="whatever")
        assert doi.doi == "whatever"

    def test_mission(self):
        """
        GIVEN Mission model
        WHEN class is instantiated
        THEN verify existence
        """
        mission = Mission(name="mission-name")
        assert mission.name == "mission-name"

    def test_instrument(self):
        """
        GIVEN Instrument model
        WHEN class is instantiated
        THEN verify existence
        """
        instrument = Instrument(name="instrument-name")
        assert instrument.name == "instrument-name"

    def test_region(self):
        """
        GIVEN Region model
        WHEN class is instantiated
        THEN verify existence
        """
        region = Region(name="region-name")
        assert region.name == "region-name"


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
