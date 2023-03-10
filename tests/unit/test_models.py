from web.models import Paper, Catalog, HpEvent, Doi, Mission, Instrument, Region


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
        c_in = Catalog()
        for event in hpevents_list:
            c_in.hp_events.append(event)
        assert len(c_in.hp_events) == 3

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
        import datetime

        assert type(hp_event_in.start_date) is datetime.datetime
        assert hp_event_in.doi.doi == "doi"
        assert hp_event_in.mission.name == "mission"
        assert hp_event_in.instrument.name == "instrument"
        assert hp_event_in.region.name == "region"

    def test_hpevent_get_dict(self, hpevent_dict_for_test):
        """
        GIVEN an hpevent dict
        WHEN HpEvent is created with that dict
        THEN verify output dict is the same
        """
        hpevent_in = HpEvent(**hpevent_dict_for_test)
        dict_out = hpevent_in.get_dict()
        assert hpevent_dict_for_test == dict_out

    # def test_hpevent_get_dict_hour(self, hpevent_dict_for_test):
    #     """
    #     GIVEN an hpevent dict
    #     WHEN HpEvent is created and saved to db
    #     THEN verify the original hour's minutes is kept
    #     """
    #     hpevent_in = HpEvent(**hpevent_dict_for_test)
    #     db.session.add(hpevent_in)
    #     db.session.commit()
    #     hp_event_out = db.session.query(HpEvent).one()
    #     dict_out = hp_event_out.get_dict()
    #     print(hp_event_out.start_date, hp_event_out.stop_date)
    #     assert hpevent_dict_for_test == dict_out

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
