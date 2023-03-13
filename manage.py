import os

import click
import redis
from pathlib import Path
from rq import Connection, Worker
from flask import current_app
from flask_migrate import upgrade
from flask.cli import FlaskGroup
from web import create_app, db
from web.models import catfile_to_db
from web.models import Paper, HpEvent

cli = FlaskGroup(create_app=create_app)


@cli.command("show_config")
def show_config():
    from pprint import pprint

    pprint(current_app.config)
    print(db.engine)


@cli.command("create_db")
def create_db():
    db.create_all()


@cli.command("refresh_events")
def refresh_events():
    """Reparse catalogs txt files

    - delete events
    - readd

    Can be used in conjonction with refresh_papers() that has to be run first.

    This method was first writen to fix the hpevent datetime value in db
    A db bug that was fixed in the commit '6b38c89 Fix the missing hours in hpevent bug'
    """
    # delete all events
    for _e in HpEvent.query.all():
        db.session.delete(_e)
        db.session.commit()
    # then parse catalogs again
    for _p in Paper.query.all():
        _p.push_cat(force=True)
        db.session.commit()


@cli.command("refresh_papers")
def refresh_papers():
    """Parse the files on disk and update db

    - delete all from db
    - parse disk and re insert pdf and txt files
    """
    for _p in Paper.query.all():
        db.session.delete(_p)
        db.session.commit()
    # Search for directories in base directory
    # that has pdf file and txt file
    # If so, build Paper and add to
    for _d in os.listdir(current_app.config["WEB_UPLOAD_DIR"]):
        found_path = os.path.join(current_app.config["WEB_UPLOAD_DIR"], _d)
        if os.path.isdir(found_path):
            pdf_file = os.path.join(found_path, _d) + ".pdf"
            try:
                cat_file = str(list(Path(found_path).glob("*bibheliotech_V1.txt"))[0])
                # cat_file.
            except IndexError:
                cat_file = "no_cat_file"
            # print (type(cat_file))
            if os.path.isfile(pdf_file) and os.path.isfile(cat_file):
                _p = Paper(title=_d, pdf_path=pdf_file, cat_path=cat_file)
                db.session.add(_p)
                db.session.commit()
                print(_p)


@cli.command("upgrade_db")
def upgrade_db():
    """Upgrade running db with new structure

    - use of the alembic method
    """
    upgrade()


@cli.command("mock_papers")
def mock_papers():
    papers_list = [
        ["aa33199-18", "aa33199-18.pdf", None, None],
        [
            "2016GL069787",
            "2016GL069787.pdf",
            "2016GL069787/1010022016gl069787_bibheliotech_V1.txt",
            None,
        ],
        [
            "5.0067370",
            "5.0067370.pdf",
            "5.0067370/10106350067370_bibheliotech_V1.txt",
            None,
        ],
    ]
    for p_l in papers_list:
        paper = Paper(title=p_l[0], pdf_path=p_l[1], cat_path=p_l[2], task_id=p_l[3])
        db.session.add(paper)
    db.session.commit()


@cli.command("list_papers")
def list_papers():
    for p in Paper.query.all():
        print(p)


@cli.command("list_events")
@click.argument("mission_id", required=False)
def list_events(mission_id=None):
    if mission_id:
        events = HpEvent.query.filter_by(mission_id=mission_id)
    else:
        events = HpEvent.query.all()
    for e in events:
        print(e)


@cli.command("feed_catalog")
@click.argument("catalog_file")
def feed_catalog(catalog_file):
    """From a catalog file, feed db with events"""
    catfile_to_db(catalog_file)


@cli.command("run_worker")
def run_worker():
    redis_url = current_app.config["REDIS_URL"]
    redis_connection = redis.from_url(redis_url)
    with Connection(redis_connection):
        worker = Worker(current_app.config["QUEUES"])
        worker.work()


if __name__ == "__main__":
    cli()
