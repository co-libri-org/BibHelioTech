from rq import get_current_job
import zipfile
import time


def get_unzip_callback(test=True):
    """Wrapper to exec a task callback depending on configuration

    @return: callback
    """

    if test:
        return unzip_mocked
    else:
        return unzip_subset


def unzip_mocked(zip_path=None, dest_folder=None):
    job = get_current_job()
    for i in range(100):
        # simulate some work
        time.sleep(0.1)
        # update progress
        job.meta['progress'] = i + 1
        job.save_meta()


def unzip_subset(zip_path, dest_folder):
    job = get_current_job()
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            files = zip_ref.namelist()
            total = len(files)
            for i, file in enumerate(files):
                zip_ref.extract(file, dest_folder)
                job.meta['progress'] = int((i + 1) / total * 100)
                job.save_meta()
        return "success"
    except Exception as e:
        job.meta['progress'] = -1
        job.save_meta()
        raise e
