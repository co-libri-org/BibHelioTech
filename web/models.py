import os.path

from web import db


class HpEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date)
    stop_date = db.Column(db.Date)
    doi_id = db.Column(db.Integer, db.ForeignKey("doi.id"), primary_key=True)
    mission_id = db.Column(db.Integer, db.ForeignKey("mission.id"), primary_key=True)
    instrument_id = db.Column(
        db.Integer, db.ForeignKey("instrument.id"), primary_key=True
    )
    region_id = db.Column(db.Integer, db.ForeignKey("region.id"), primary_key=True)
    doi = db.relationship("Doi", back_populates="hp_events")
    mission = db.relationship("Mission", back_populates="hp_events")
    instrument = db.relationship("Instrument", back_populates="hp_events")
    region = db.relationship("Region", back_populates="hp_events")


class Doi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doi = db.Column(db.String, unique=True, nullable=False)
    hp_events = db.relationship("HpEvent", back_populates="doi")

    def __init__(self, doi):
        self.doi = doi


class Mission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    hp_events = db.relationship("HpEvent", back_populates="mission")

    def __init__(self, name):
        self.name = name


class Instrument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    hp_events = db.relationship("HpEvent", back_populates="instrument")

    def __init__(self, name):
        self.name = name


class Region(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    hp_events = db.relationship("HpEvent", back_populates="region")

    def __init__(self, name):
        self.name = name


class Paper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    pdf_path = db.Column(db.String, unique=True, nullable=False)
    cat_path = db.Column(db.String, unique=True)
    task_id = db.Column(db.String, unique=True)

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
