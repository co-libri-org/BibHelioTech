import datetime
import os.path
import csv

from web import db

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"


# TOOLS TO INSERT IN MODELS METHODS
def catfile_to_rows(catfile):
    """Get all rows of a catalog file as  dict

      TODO: should move to Paper or Catalog method

       -  read each line, rid of comments
       -  create a hp_event_dict
    :return: hpevent_dict list
    """
    hpeventdict_list = []
    with open(catfile, newline="") as csvfile:
        reader = csv.reader(
            filter(lambda r: r[0] != "#", csvfile), delimiter=" ", quotechar='"'
        )
        for row in reader:
            hpevent_dict = {
                "start_date": row[0],
                "stop_date": row[1],
                "doi": row[2],
                "mission": row[3],
                "instrument": row[4],
                "region": row[5],
            }

            hpeventdict_list.append(hpevent_dict)
    return hpeventdict_list


def catfile_to_db(catfile):
    """Save a catalog file's content to db as hpevents

    TODO: should move to Paper or Catalog method

    :return: nothing
    """
    for hpevent_dict in catfile_to_rows(catfile):
        hpevent = HpEvent(**hpevent_dict)
        db.session.add(hpevent)
    db.session.commit()


class Catalog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hp_events = db.relationship("HpEvent", back_populates="catalog")


class HpEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date)
    stop_date = db.Column(db.Date)
    doi_id = db.Column(db.Integer, db.ForeignKey("doi.id"))
    mission_id = db.Column(db.Integer, db.ForeignKey("mission.id"))
    instrument_id = db.Column(db.Integer, db.ForeignKey("instrument.id"))
    region_id = db.Column(db.Integer, db.ForeignKey("region.id"))
    doi = db.relationship("Doi", back_populates="hp_events")
    mission = db.relationship("Mission", back_populates="hp_events")
    instrument = db.relationship("Instrument", back_populates="hp_events")
    region = db.relationship("Region", back_populates="hp_events")

    catalog = db.relationship("Catalog", back_populates="hp_events")
    catalog_id = db.Column(db.Integer, db.ForeignKey("catalog.id"))

    def __init__(
        self,
        start_date: str,
        stop_date: str,
        doi: str,
        mission: str,
        instrument: str,
        region: str,
    ):
        self.start_date = datetime.datetime.strptime(start_date, DATE_FORMAT)
        self.stop_date = datetime.datetime.strptime(stop_date, DATE_FORMAT)
        self.set_doi(doi)
        self.set_mission(mission)
        self.set_instrument(instrument)
        self.set_region(region)

    def __repr__(self):
        r_str = f"{self.start_date} {self.stop_date} {self.doi.doi} {self.mission_id}:{self.mission.name} {self.instrument.name}"
        return r_str

    def get_dict(self):
        r_dict = {
            "start_date": datetime.datetime.strftime(self.start_date, DATE_FORMAT)[
                0:-3
            ],
            "stop_date": datetime.datetime.strftime(self.stop_date, DATE_FORMAT)[0:-3],
            "doi": self.doi.doi,
            "mission": self.mission.name,
            "instrument": self.instrument.name,
            "region": self.region.name,
        }
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


class Doi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doi = db.Column(db.String, unique=True, nullable=False)
    hp_events = db.relationship("HpEvent", back_populates="doi")


class Mission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    hp_events = db.relationship("HpEvent", back_populates="mission")


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
    pdf_path = db.Column(db.String, unique=True, nullable=False)
    cat_path = db.Column(db.String, unique=True)
    task_id = db.Column(db.String, unique=True)
    cat_in_db = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Paper {self.id} {self.title} {self.pdf_path} {self.cat_path} {self.task_id}>"

    def set_task_id(self, task_id):
        self.task_id = task_id
        db.session.add(self)
        db.session.commit()

    def set_cat_path(self, cat_path):
        self.cat_path = cat_path
        db.session.add(self)
        db.session.commit()

    def push_cat(self):
        """Insert our catalog's events to db"""
        print("Do we :", self.cat_in_db)
        print("Do we :", self.has_cat)
        if not self.cat_in_db and self.has_cat:
            self.cat_in_db = True
            catfile_to_db(self.cat_path)

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
