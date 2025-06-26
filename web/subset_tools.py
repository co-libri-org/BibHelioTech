import os.path

from flask import current_app
from rq import get_current_job
import zipfile
import time


def job_by_subset(subset_name):
    # Now, retrieve jobid by filename stored at job start
    job_id_bytes = current_app.redis_conn.get(f"job_by_filename:{subset_name}")
    if job_id_bytes is not None:
        job_id = job_id_bytes.decode()  # Conversion bytes -> str
    else:
        job_id = None
    return job_id


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

    subset_name, zip_ext = os.path.splitext( os.path.basename(zip_path))
    job_id = job_by_subset(subset_name)
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
        time.sleep(0.1)
        # update progress
        job.meta['progress'] = f" {int((i + 1) / total_files * 100)}%"
        job.save_meta()


def unzip_subset(zip_path, zip_folder, zip_files=None):
    job = get_current_job()
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            files = zip_ref.namelist()
            total = len(files)
            for i, file in enumerate(files):
                zip_ref.extract(file, zip_folder)
                job.meta['progress'] = int((i + 1) / total * 100)
                job.save_meta()
        return "success"
    except Exception as e:
        job.meta['progress'] = -1
        job.save_meta()
        raise e
