import json
import os.path
import re

from flask import current_app
from rq import get_current_job
from rq.exceptions import NoSuchJobError
from rq.job import Job
import zipfile
import time

from web import db
from web.models import Paper

ISTEX_SUBSET_PATTERN = r"^istex-subset-\d{4}-\d{2}-\d{2}$"
ISTEX_ZIP_PATTERN = rf"{ISTEX_SUBSET_PATTERN[:-1]}.zip$"

JOB_BY_FILENAME_KEY = "job_by_filename"


class Subset:
    def __init__(self, _subset_name):
        self.size = None
        self.nb_json = None
        self.name = _subset_name
        self.base_dir = current_app.config['ZIP_UPLOAD_DIR']
        self.set_archive_info()

    @property
    def status(self):
        return "extracted" if self.extracted else "zipped"

    @property
    def extracted(self):
        return self.directory is not None

    @property
    def directory(self):
        _subset_dir = os.path.join(self.base_dir, self.name)
        if not (re.match(ISTEX_SUBSET_PATTERN, str(self.name))
                and os.path.isdir(_subset_dir)):
            return None
        return _subset_dir

    @property
    def papers(self):
        _papers = []
        if self.directory is None:
            return _papers
        _subset_dir = str(self.directory)
        existing_papers = {p.istex_id: p for p in db.session.query(Paper).all()}

        for _dir in (d for d in os.scandir(_subset_dir) if d.is_dir()):
            _abs_dir = _dir.path
            _name = _dir.name
            _paper_json = os.path.join(_abs_dir, f"{_name}.json")
            _paper_cleaned = os.path.join(_abs_dir, f"{_name}.cleaned")
            if not (os.path.isfile(_paper_json) and os.path.isfile(_paper_cleaned)):
                continue
            with open(_paper_json) as pj:
                _meta = json.load(pj)

            paper = existing_papers.get(_name)
            if paper is not None:
                _in_db = True
                _db_id = paper.id
            else:
                _in_db = False
                _db_id = None

            _papers.append(
                {'id': _db_id, 'name': _dir, 'title': _meta["title"], 'json': _paper_json, 'cleaned': _paper_cleaned,
                 'in_db': _in_db})
        return _papers

    def set_archive_info(self):
        import math
        import zipfile
        # archive size in Mo
        zip_path = os.path.join(self.base_dir, f"{self.name}.zip")
        size_octets = os.path.getsize(zip_path)
        size_mo = size_octets / (1024 * 1024)
        self.size = f"{math.ceil(size_mo)} Mo"

        # Count JSON files contained in archive
        with zipfile.ZipFile(zip_path, 'r') as archive:
            json_files = [f for f in archive.namelist() if f.endswith('.json')]
            self.nb_json = len(json_files)

    @property
    def job(self):
        return Job.fetch(self.task_id, connection=current_app.redis_conn)  # type: ignore[attr-defined]

    @property
    def task_status(self):
        return self.job.get_status(refresh=True).value

    @property
    def task_progress(self):
        return self.job.meta.get("progress")

    @property
    def task_id(self):
        # Now, retrieve jobid by filename stored at job start
        task_id_bytes = current_app.redis_conn.get(f"{JOB_BY_FILENAME_KEY}:{self.name}")  # type: ignore[attr-defined]
        if task_id_bytes is None:
            raise NoSuchJobError
        task_id = task_id_bytes.decode()  # Conversion bytes -> str
        return task_id

    def set_task_id(self, task_id):
        current_app.redis_conn.set(f"{JOB_BY_FILENAME_KEY}:{self.name}", task_id)  # type: ignore[attr-defined]


def get_unzip_callback(test=True):
    """Wrapper to exec a task callback depending on configuration

    @return: callback
    """

    if test:
        return unzip_mocked
    else:
        return unzip_subset


def unzip_mocked(_zip_path, _zip_folder, total_files):
    job = get_current_job()
    for i in range(total_files):
        # simulate some work
        time.sleep(0.001)
        # update progress
        job.meta['progress'] = f" {int((i + 1) / total_files * 100)}%"
        job.save_meta()


def unzip_subset(zip_path, dst_folder, _zip_files=None):
    job = get_current_job()
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            files = zip_ref.namelist()
            total = len(files)
            for i, file in enumerate(files):
                zip_ref.extract(file, dst_folder)
                job.meta['progress'] = f"{int((i + 1))} / {total} "
                job.save_meta()
        return "success"
    except Exception as e:
        job.meta['progress'] = -1
        job.save_meta()
        raise e
