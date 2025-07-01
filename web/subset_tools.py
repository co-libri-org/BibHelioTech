import json
import os.path
import re

from redis.connection import ConnectionError
from flask import current_app
from rq import get_current_job
import zipfile
import time

from web import db
from web.models import Paper

ISTEX_SUBSET_PATTERN = r"^istex-subset-\d{4}-\d{2}-\d{2}$"
ISTEX_ZIP_PATTERN = rf"{ISTEX_SUBSET_PATTERN[:-1]}.zip$"


class Subset:
    def __init__(self, _subset_name):
        self.name = _subset_name

    @property
    def extracted(self):
        return self.directory is not None

    @property
    def directory(self):
        base_dir = current_app.config['ZIP_UPLOAD_DIR']
        _subset_dir = os.path.join(base_dir, self.name)
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

    @property
    def task_id(self):
        # Now, retrieve jobid by filename stored at job start
        task_id_bytes = current_app.redis_conn.get(f"task_by_filename:{self.name}")
        if task_id_bytes is not None:
            task_id = task_id_bytes.decode()  # Conversion bytes -> str
        else:
            task_id = None
        return task_id

    def set_task_id(self, task_id):
        current_app.redis_conn.set(f"job_by_filename:{self.name}", task_id)


def zip_archive_info(zip_path):
    import math
    import zipfile
    # archive size in Mo
    size_octets = os.path.getsize(zip_path)
    size_mo = size_octets / (1024 * 1024)
    size_mo = f"{math.ceil(size_mo)} Mo"

    # Count JSON files contained in archive
    with zipfile.ZipFile(zip_path, 'r') as archive:
        json_files = [f for f in archive.namelist() if f.endswith('.json')]
        nb_json = len(json_files)

    subset_name, zip_ext = os.path.splitext(os.path.basename(zip_path))
    try:
        job_id = job_by_subset(subset_name)
    except ConnectionError:
        job_id = None
    return subset_name, size_mo, nb_json, job_id


def get_unzip_callback(test=True):
    """Wrapper to exec a task callback depending on configuration

    @return: callback
    """

    if test:
        return unzip_mocked
    else:
        return unzip_subset


def unzip_mocked(zip_path, zip_folder, total_files):
    job = get_current_job()
    for i in range(total_files):
        # simulate some work
        time.sleep(0.001)
        # update progress
        job.meta['progress'] = f" {int((i + 1) / total_files * 100)}%"
        job.save_meta()


def unzip_subset(zip_path, dst_folder, zip_files=None):
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
