import datetime
import json
import os
import os.path
from enum import StrEnum, auto
from json import JSONDecodeError
from typing import Optional

import filetype
from sqlalchemy.exc import IntegrityError

from werkzeug.utils import secure_filename

from bht.catalog_tools import catfile_to_rows
from web import db
from web.errors import IstexError, FilePathError, DbError
from web.istex_proxy import ark_to_id, get_doc_url, istex_doc_to_struct

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


def istexdir_to_db(_istex_dir, upload_dir, file_ext="cleaned"):
    """
    Read a dir containing a .cleaned file and a .json file with meta info
    Add the file in database for later processing
    """
    istex_id = os.path.basename(_istex_dir)
    istex_file_name = f"{istex_id}.{file_ext}"
    istex_file_path = os.path.join(_istex_dir, istex_file_name)
    json_file_path = os.path.join(_istex_dir, f"{istex_id}.json")
    if not os.path.isdir(_istex_dir) \
            or not os.path.isfile(istex_file_path) \
            or not os.path.isfile(json_file_path):
        raise FilePathError(f"Istex dir has wrong structure")
    # read  json in dir
    with open(json_file_path) as json_fp:
        try:
            document_json = json.load(json_fp)
        except JSONDecodeError:
            print(f"Couldnt read json file {json_file_path}")
            return None

    istex_struct = istex_doc_to_struct(document_json)

    with open(istex_file_path) as _ifd:
        stream_to_db(_ifd.read().encode("UTF-8"), istex_file_name, upload_dir, istex_struct)


def istexjson_to_db(json_file, upload_dir, file_ext="cleaned", force_update=False):
    """
    Read the json meta-info file of an istex directory
        get the article file
        add to db for late usage

    :param force_update:
    :param json_file:
    :param upload_dir:
    :param file_ext:
    :return:
    """
    if not os.path.isfile(json_file):
        raise FilePathError(f"Couldn't find {json_file}")

    with open(json_file) as json_fp:
        try:
            document_json = json.load(json_fp)
        except JSONDecodeError:
            print(f"Couldn't read json file {json_file}")
            return None

    try:
        istex_struct = istex_doc_to_struct(document_json)
    except KeyError as e:
        return {'status': 'failed', 'reason': str(e)}

    paper = Paper.query.filter_by(istex_id=istex_struct['istex_id']).one_or_none()

    if paper is None:
        istex_struct['status'] = "added"
    elif type(paper) == Paper:
        if force_update:
            istex_struct['status'] = "updated"
        else:
            istex_struct['status'] = "skipped"
            istex_struct['paper_id'] = paper.id
            return istex_struct

    istex_file_path = json_file.replace("json", file_ext)
    istex_file_name = os.path.basename(istex_file_path)

    with open(istex_file_path) as _ifd:
        try:
            paper_id = stream_to_db(_ifd.read().encode("UTF-8"), istex_file_name, upload_dir, istex_struct)
            istex_struct['paper_id'] = paper_id
        except DbError as e:
            return {'status': 'failed', 'reason': str(e)}
    return istex_struct


def stream_to_db(file_stream, filename, upload_dir, istex_struct=None, force_copy=False):
    """
    Push Paper to db from a stream
    (update Paper's content if exists)

        - write content to destination file
        - add new Paper object to db

    :param force_copy:
    :param upload_dir:
    :param istex_struct:
    :param file_stream the file content
    :param filename
    :return: the paper's id, or None if couldn't do it
    """
    filename = secure_filename(filename)
    if not os.path.isdir(upload_dir):
        os.makedirs(upload_dir)
    _file_path = os.path.join(upload_dir, filename)

    # Copy filestream unless file already exists or force
    if not os.path.isfile(_file_path) or force_copy:
        with open(_file_path, "wb") as _fd:
            _fd.write(file_stream)
    else:
        print(f"                                                  {filename} exists, dont overwrite", end="\r")
    if not os.path.isfile(_file_path):
        raise FilePathError(f"There was an error on {filename} copy")
    _guessed_filetype = filetype.guess(_file_path)
    _split_filename = os.path.splitext(filename)
    _file_type = None
    if _guessed_filetype and _guessed_filetype.mime == "application/pdf":
        _file_type = BhtFileType.PDF
    elif _split_filename[1] in [".cleaned", ".txt"]:
        _file_type = BhtFileType.TXT
    else:
        return None
    if istex_struct is not None:
        _paper_title = istex_struct["title"]
    else:
        _paper_title = _split_filename[0]
    paper = Paper.query.filter_by(title=_paper_title).one_or_none()
    if paper is None:
        paper = Paper(title=_paper_title)

    # set_file_path() will add and commit paper
    paper.set_file_path(_file_path, _file_type)
    if istex_struct is not None:
        try:
            paper.set_doi(istex_struct["doi"])
            paper.set_ark(istex_struct["ark"])
            paper.set_pubdate(istex_struct["pub_date"])
            paper.set_istex_id(istex_struct["istex_id"])
        except IntegrityError:
            db.session.rollback()
            raise DbError("Uniq field already exists")
    return paper.id


def catfile_to_db(catfile):
    """Save a catalog file's content to db as hpevents

    :return: nothing
    """
    with db.session.no_autoflush:
        for hpevent_dict in catfile_to_rows(catfile):
            # skip if row is empty
            if not hpevent_dict:
                continue
            hpevent = HpEvent(**hpevent_dict)
            db.session.add(hpevent)
            db.session.commit()


class TaskStruct:
    """
    Represents the status of a paper processing task
    """
    task_started: Optional[datetime] = None
    task_stopped: Optional[datetime] = None

    def __init__(self, paper: 'Paper'):
        self.paper = paper
        self.task_started = None if paper.task_started is None else paper.task_started.replace(
            tzinfo=datetime.timezone.utc)
        self.task_stopped = None if paper.task_stopped is None else paper.task_stopped.replace(
            tzinfo=datetime.timezone.utc)
        self.cat_is_processed = paper.has_cat and paper.cat_in_db


class HpEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.DateTime)
    stop_date = db.Column(db.DateTime)
    paper_id = db.Column(db.Integer, db.ForeignKey("paper.id"), nullable=False)
    mission_id = db.Column(db.Integer, db.ForeignKey("mission.id"))
    instrument_id = db.Column(db.Integer, db.ForeignKey("instrument.id"))
    region_id = db.Column(db.Integer, db.ForeignKey("region.id"))
    conf = db.Column(db.Float)
    d = db.Column(db.Integer)
    r = db.Column(db.Integer)

    paper = db.relationship("Paper", back_populates="hp_events")
    mission = db.relationship("Mission", back_populates="hp_events")
    instrument = db.relationship("Instrument", back_populates="hp_events")
    region = db.relationship("Region", back_populates="hp_events")

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

    @classmethod
    def get_events_dicts(cls, events):
        """From an event list to a list of event's dict with maxconf calculation once only """
        if not events:
            return []

        # dynamical max_conf calculation on the whole database
        max_conf = max(event.conf for event in events if event.conf is not None) if events else 1

        return [event.get_dict(max_conf) for event in events]

    def get_dict(self, max_conf):
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

    hp_events = db.relationship("HpEvent", back_populates="paper")

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
        task_status: {self.task_status}
        task_started: {self.task_started}
        task_stopped: {self.task_stopped}
        pipe_ver:  {self.pipeline_version}>"""

    def __str__(self):
        title = f"'{self.title[:20]}...'"
        status = f"'{self.task_status}'"
        started = str(self.task_started)[:19] if self.task_started is not None else "-" * 19
        stopped = str(self.task_stopped)[:19] if self.task_stopped is not None else "-" * 19
        return (f"<Paper #{self.id:<5}"
                f" {title:25}"
                f" has_cat:{self.has_cat:2}"
                f" status:{status:10} {started:20} -> {stopped:20}"
                f" version: {self.pipeline_version}>")

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
        if not self.has_cat:
            return
        self.clean_events()
        for hpevent_dict in catfile_to_rows(self.cat_path):
            # skip if row is empty
            if not hpevent_dict:
                continue
            hpevent = HpEvent(**hpevent_dict)
            self.hp_events.append(hpevent)
        self.cat_in_db = True
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
        Remove the list of events with the same DOI as ours.
        TODO: it might be better to set a relationship between HpEvent and Paper models.

        @return: None
        """
        self.hp_events.clear()
        self.cat_in_db = False
        db.session.commit()

    def get_events(self):
        """
        Return the list of events with same doi as our's
        #TODO: DB_REFACTOR should be better to set a new relationship between HpEvent and Paper models
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
        TODO: DB_REFACTOR better set  at self.push_cat(), and better filter from cat_path
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
