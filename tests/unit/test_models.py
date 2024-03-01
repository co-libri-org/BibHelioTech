from datetime import datetime

from web.models import (
    Paper,
    Catalog,
    HpEvent,
    Doi,
    Mission,
    Instrument,
    Region,
    catfile_to_rows,
    catfile_to_db,
    rows_to_catstring,
)


class TestTask:
    def test_paper_set_taskid(self, paper_for_test, db):
        task_id = "this_is_a_task_id"
        paper_for_test.set_task_id(task_id)
        p = db.session.get(Paper, paper_for_test.id)
        assert p.task_id == task_id

    def test_paper_set_taskstatus(self, paper_for_test, db):
        task_status = "this_is_a_task_status"
        paper_for_test.set_task_status(task_status)
        p = db.session.get(Paper, paper_for_test.id)
        assert p.task_status == task_status

    def test_paper_set_taskstarted(self, paper_for_test, db):
        task_started = datetime.now()
        paper_for_test.set_task_started(task_started)
        p = db.session.get(Paper, paper_for_test.id)
        assert p.task_started == task_started

    def test_paper_set_taskstopped(self, paper_for_test, db):
        task_stopped = datetime.now()
        paper_for_test.set_task_stopped(task_stopped)
        p = db.session.get(Paper, paper_for_test.id)
        assert p.task_stopped == task_stopped


class TestDb:
    def test_db_created(self, db):
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

    def test_paper_set_pubdate(self):
        """
        GIVEN Paper model
        WHEN pubdate is set
        THEN verify it was stored
        """
        paper = Paper(title="title", pdf_path="path", publication_date="2015")
        assert paper.publication_date == "2015"
        paper.set_pubdate("2020")
        assert paper.publication_date == "2020"

    def test_paper_set_istexid(self):
        """
        GIVEN Paper model
        WHEN pubdate is set
        THEN verify it was stored
        """
        paper = Paper(title="title", pdf_path="path")
        paper.set_pubdate("ANANANANAN")
        assert paper.publication_date == "ANANANANAN"

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
        # assert paper_for_test.cat_in_db

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


class TestCatTools:
    def test_catfile_to_rows(self, cat_for_test):
        hp_events = catfile_to_rows(cat_for_test)
        assert len(hp_events) == 46

    def test_catfile_to_db(self, cat_for_test, db):
        catfile_to_db(cat_for_test)
        allevents = db.session.query(HpEvent).all()
        assert len(allevents) == 46

    def test_rows_to_catstring(self, cat_for_test):
        hp_events = catfile_to_rows(cat_for_test)
        cat_str = rows_to_catstring(hp_events, "what")
        assert len(cat_str) == 6900
