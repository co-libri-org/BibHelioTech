import datetime
import os.path
from enum import StrEnum, auto

from requests import session

from bht.catalog_tools import catfile_to_rows
from web import db
from web.errors import IstexError
from web.istex_proxy import ark_to_id, get_doc_url

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"


# TODO: REFACTOR choose between BhtFileType or  web.istex_proxy.IstexDocType
class BhtFileType(StrEnum):
    PDF = auto()
    TXT = auto()
    CAT = auto()


# TOOLS TO INSERT IN MODELS METHODS


def istexid_to_paper(istex_id):
    paper = db.session.query(Paper).filter_by(istex_id=istex_id).one_or_none()
    return paper


# TODO: MODEL warning raised because HpEvent not in session when __init__ see test_catfile_to_db
def catfile_to_db(catfile):
    """Save a catalog file's content to db as hpevents

    TODO: MODEL should move to Paper or Catalog method

    :return: nothing
    """
    for hpevent_dict in catfile_to_rows(catfile):
        # skip if row is empty
        if not hpevent_dict:
            continue
        hpevent = HpEvent(**hpevent_dict)
        db.session.add(hpevent)
        db.session.commit()


class Catalog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hp_events = db.relationship("HpEvent", back_populates="catalog")


class HpEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.DateTime)
    stop_date = db.Column(db.DateTime)
    doi_id = db.Column(db.Integer, db.ForeignKey("doi.id"))
    mission_id = db.Column(db.Integer, db.ForeignKey("mission.id"))
    instrument_id = db.Column(db.Integer, db.ForeignKey("instrument.id"))
    region_id = db.Column(db.Integer, db.ForeignKey("region.id"))
    doi = db.relationship("Doi", back_populates="hp_events")
    mission = db.relationship("Mission", back_populates="hp_events")
    instrument = db.relationship("Instrument", back_populates="hp_events")
    region = db.relationship("Region", back_populates="hp_events")
    conf = db.Column(db.Float)
    d = db.Column(db.Integer)
    r = db.Column(db.Integer)

    catalog = db.relationship("Catalog", back_populates="hp_events")
    catalog_id = db.Column(db.Integer, db.ForeignKey("catalog.id"))

    # TODO: MODEL warning raised because HpEvent not in session when __init__ see test_catfile_to_db
    def __init__(
        self,
        start_time: str,
        stop_time: str,
        doi: str,
        sats: str,
        insts: str,
        regs: str,
        conf: float = None,
        d: int = None,
        r: int = None,
        **kwargs,
    ):
        self.start_date = datetime.datetime.strptime(start_time, DATE_FORMAT)
        self.stop_date = datetime.datetime.strptime(stop_time, DATE_FORMAT)
        self.set_doi(doi)
        self.set_mission(sats)
        self.set_instrument(insts)
        self.set_region(regs)
        self.set_conf(conf)
        self.set_d(d)
        self.set_r(r)

    def __repr__(self, full=False):
        full_str = f"{self.start_date} {self.stop_date} {self.doi.doi} {self.mission.name:20}\
        {self.instrument.name} D:{self.d} R:{self.r} Conf:{self.conf}"
        short_str = f"{self.start_date} {self.stop_date} {self.mission.name:20}\
         {self.d:>4} {self.r:>4} {self.conf:>6}"
        r_str = full_str if full else short_str

        return r_str

    def get_dict(self):
        td = self.stop_date - self.start_date
        duration = datetime.timedelta(days=td.days, seconds=td.seconds, microseconds=0)
        hours_str = f"{duration}"[-8:]
        days = int(duration.days)
        duration_str = f"{days:4}d {hours_str:>8}"

        r_dict = {
            "id": self.id,
            "start_date": datetime.datetime.strftime(self.start_date, DATE_FORMAT)[
                0:-3
            ],
            "stop_date": datetime.datetime.strftime(self.stop_date, DATE_FORMAT)[0:-3],
            "duration": duration,
            "duration_str": duration_str,
            "doi": self.doi.doi,
            "mission": self.mission.name,
            "instrument": self.instrument.name,
            "region": self.region.name,
            "conf": self.conf,
            "d": self.d,
            "r": self.r,
        }
        # normalize conf index on the whole database
        all_events = HpEvent.query.all()
        max_conf = max([_e.conf for _e in all_events])
        r_dict["nconf"] = 1.0 - r_dict["conf"] / max_conf
        return r_dict

    def set_doi(self, doi_str):
        doi = db.session.query(Doi).filter_by(doi=doi_str).one_or_none()
        if doi is None:
            doi = Doi(doi=doi_str)
        self.doi = doi

    def set_mission(self, mission_str):
        mission = db.session.query(Mission).filter_by(name=mission_str).one_or_none()
        if mission is None:
            mission = Mission(name=mission_str)
        self.mission = mission

    def set_instrument(self, instr_str):
        instrument = (
            db.session.query(Instrument).filter_by(name=instr_str).one_or_none()
        )
        if instrument is None:
            instrument = Instrument(name=instr_str)
        self.instrument = instrument

    def set_region(self, region_str):
        region = db.session.query(Region).filter_by(name=region_str).one_or_none()
        if region is None:
            region = Region(name=region_str)
        self.region = region

    def set_conf(self, conf: float):
        self.conf = conf

    def set_d(self, d: int):
        self.d = d

    def set_r(self, r: int):
        self.r = r


class Doi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doi = db.Column(db.String, unique=True, nullable=False)
    hp_events = db.relationship("HpEvent", back_populates="doi")


class Mission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    hp_events = db.relationship("HpEvent", back_populates="mission")

    def __repr__(self):
        return f"""<Mission #{self.id:<2} name: {self.name:15} num events: {len(self.hp_events):3}"""


class Instrument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    hp_events = db.relationship("HpEvent", back_populates="instrument")


class Region(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    hp_events = db.relationship("HpEvent", back_populates="region")


class Paper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    doi = db.Column(db.String, unique=True)
    ark = db.Column(db.String, unique=True)
    istex_id = db.Column(db.String, unique=True)
    publication_date = db.Column(db.String)
    pdf_path = db.Column(db.String, unique=True)
    txt_path = db.Column(db.String, unique=True)
    cat_path = db.Column(db.String, unique=True)
    # TODO: change for method/property  ?
    cat_in_db = db.Column(db.Boolean, default=False)
    # TODO: MODEL move to Task model ( and relative setters )
    task_id = db.Column(db.String, unique=True)
    task_status = db.Column(db.String)
    task_started = db.Column(db.DateTime)
    task_stopped = db.Column(db.DateTime)

    def __repr__(self):
        return f"""<Paper #{self.id}
        title:     {self.title}
        doi:       {self.doi}
        ark:       {self.ark}
        istex_id:  {self.istex_id}
        pdf:       {self.pdf_path}
        txt:       {self.txt_path}
        cat:       {self.cat_path}
        cat_in_db: {self.cat_in_db}
        pipe_ver:  {self.pipeline_version}>"""

    def set_task_id(self, task_id):
        self.task_id = task_id
        db.session.add(self)
        db.session.commit()

    def set_task_status(self, task_status):
        self.task_status = task_status
        db.session.add(self)
        db.session.commit()

    def set_task_started(self, task_started):
        self.task_started = task_started
        db.session.add(self)
        db.session.commit()

    def set_task_stopped(self, task_stopped):
        self.task_stopped = task_stopped
        db.session.add(self)
        db.session.commit()

    def set_file_path(self, file_path, file_type):
        if file_type == BhtFileType.PDF:
            self.pdf_path = file_path
        elif file_type == BhtFileType.TXT:
            self.txt_path = file_path
        db.session.add(self)
        db.session.commit()

    def set_cat_path(self, cat_path):
        self.cat_path = cat_path
        self.cat_in_db = False
        db.session.add(self)
        db.session.commit()

    def set_doi(self, doi):
        self.doi = doi
        db.session.add(self)
        db.session.commit()

    def set_ark(self, ark):
        self.ark = ark
        db.session.add(self)
        db.session.commit()

    def set_pubdate(self, pub_date):
        self.publication_date = pub_date
        db.session.add(self)
        db.session.commit()

    def set_istex_id(self, istex_id):
        self.istex_id = istex_id
        db.session.add(self)
        db.session.commit()

    def push_cat(self, force=False):
        """Insert our catalog's events to db"""
        # Quit if already added and not force
        if self.cat_in_db and not force:
            return
        # only if there is a file
        if self.has_cat:
            self.clean_events()
            catfile_to_db(self.cat_path)
            self.cat_in_db = True
        db.session.add(self)
        db.session.commit()

    def istex_update(self):
        """From our ids, update meta information from istex api"""
        if self.istex_id is None:
            if self.ark:
                self.istex_id = ark_to_id(self.ark)
            elif self.has_txt:
                self.istex_id = os.path.basename(self.txt_path).split(".")[0]
            elif self.has_pdf:
                self.istex_id = os.path.basename(self.pdf_path).split(".")[0]
            else:
                raise IstexError("Unable to grap meta info")
        istex_struct = get_doc_url(self.istex_id)
        self.title = istex_struct["title"]
        self.doi = istex_struct["doi"]
        self.ark = istex_struct["ark"]
        self.publication_date = istex_struct["pub_date"]
        db.session.add(self)
        db.session.commit()

    def clean_events(self):
        """
        Remove the list of events with same doi as our's
        #TODO: should be better to set a new relationship between HpEvent and Paper models
        @return:  None
        """
        for _e in self.get_events():
            db.session.delete(_e)
        self.cat_in_db = False
        db.session.commit()

    def get_events(self):
        """
        Return the list of events with same doi as our's
        #TODO: should be better to set a new relationship between HpEvent and Paper models
        @return:  list of HpEvents
        """
        found_events = []
        doi = Doi.query.filter_by(doi=self.doi).one_or_none()
        if doi is not None:
            found_events = HpEvent.query.filter_by(doi_id=doi.id).all()
        return found_events

    @property
    def pipeline_version(self):
        """
        Read from catalog file and grab pipeline version number
        """
        import re

        version_number = "0.0"
        if not self.has_cat:
            return version_number
        p = re.compile(r"# BibHelioTechVersion: V(\d[\d.]*);")
        with open(self.cat_path) as f:
            lines = f.readlines()
            for _l in lines:
                _m = p.match(_l)
                if _m is not None:
                    version_number = _m.group(1)
                    break

        return version_number

    @property
    def has_cat(self):
        try:
            has_cat = os.path.isfile(self.cat_path)
        except TypeError:
            has_cat = False
        return has_cat

    @property
    def has_pdf(self):
        try:
            has_pdf = os.path.isfile(self.pdf_path)
        except TypeError:
            has_pdf = False
        return has_pdf

    @property
    def has_txt(self):
        try:
            has_txt = os.path.isfile(self.txt_path)
        except TypeError:
            has_txt = False
        return has_txt
