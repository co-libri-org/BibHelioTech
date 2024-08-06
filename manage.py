import os
import shutil

import click
import redis
from pathlib import Path
from rq import Connection, Worker
from flask import current_app
from flask_migrate import upgrade
from flask.cli import FlaskGroup
from web import create_app, db
from web.bht_proxy import pipe_paper
from web.models import catfile_to_db
from web.models import Paper, HpEvent

cli = FlaskGroup(create_app=create_app)


@cli.command("show_config")
def show_config():
    """List all config variables values"""

    for k, v in current_app.config.items():
        print(f"{k:30} {v}")
    print(db.engine)


@cli.command("create_db")
def create_db():
    """Create db file if it doesn't exist"""
    db.create_all()


@cli.command("upgrade_db")
def upgrade_db():
    """Upgrade running db with new structure

    - use of the alembic method
    """
    upgrade()


@cli.command("run_worker")
def run_worker():
    """Run a rq worker that will listen to incoming tasks

    \b
    It is necessary to run it through a Flask context as we use the sqlalchemy library.

    \b
    Will also be useful in a docker container. See in docker-compose.yml the 'worker' service.
    """

    redis_url = current_app.config["REDIS_URL"]
    redis_connection = redis.from_url(redis_url)
    worker = Worker(current_app.config["QUEUES"], connection=redis_connection)
    worker.work()


@cli.command("list_papers")
def list_papers():
    """Show all papers contained in database"""
    for p in Paper.query.all():
        print(p)


@cli.command("update_paper")
@click.option("-c", "--cat-path", "cat_path")
@click.argument("paper_id", required=True)
def update_paper_catpath(paper_id, cat_path):
    """Set new paper's catpath"""
    p = db.session.get(Paper, paper_id)
    p.set_cat_path(cat_path)


@cli.command("show_paper")
@click.argument("paper_id", required=True)
def show_paper(paper_id):
    """Display paper's content by id"""
    p = db.session.get(Paper, paper_id)
    print(p)


@cli.command("del_paper")
@click.argument("paper_id", required=True)
def del_paper(paper_id):
    """Remove from database the record by id"""
    p = db.session.get(Paper, paper_id)
    db.session.delete(p)
    db.session.commit()


@cli.command("clone_paper")
@click.argument("paper_id", required=True)
def clone_paper(paper_id):
    """Copy an already existing paper

    Will create a new record in the database,
    prepending 'COPY-' string at the beginning of each class attribute.
    """

    def clone_copy(orig_path):
        _dirname = os.path.dirname(orig_path)
        _basename = os.path.basename(orig_path)
        _filename, _extension = os.path.splitext(_basename)
        _cloned_path = os.path.join(_dirname, f"{_filename}-copy{_extension}")
        shutil.copy(orig_path, _cloned_path)
        return _cloned_path

    p_orig = db.session.get(Paper, paper_id)
    cloned_pdf_path = None
    cloned_txt_path = None
    if p_orig.has_pdf:
        cloned_pdf_path = clone_copy(p_orig.pdf_path)
    if p_orig.has_txt:
        cloned_txt_path = clone_copy(p_orig.txt_path)
    p_cloned = Paper(
        title=f"COPY-{p_orig.title}",
        doi=f"COPY-{p_orig.doi}",
        ark=f"COPY-{p_orig.ark}",
        istex_id=f"COPY-{p_orig.istex_id}",
        publication_date=p_orig.publication_date,
        pdf_path=cloned_pdf_path,
        txt_path=cloned_txt_path,
    )
    db.session.add(p_cloned)
    db.session.commit()
    print(p_cloned)


@cli.command("run_paper")
@click.argument("paper_id", required=True)
def run_paper(paper_id):
    """Run the latest pipeline on that paper's article"""
    _p_id = pipe_paper(paper_id)
    print(f"Pipeline run on paper: {_p_id}.")


@cli.command("run_papers")
def run_papers():
    """Run the latest pipeline on all papers"""
    for p in Paper.query.all():
        print(f"Running pipeline on paper {p.id}")
        try:
            _p_id = pipe_paper(p.id)
        except Exception as e:
            print(f"Couldn't run on paper #{p.id}")


@cli.command("refresh_papers")
def refresh_papers():
    """Parse the files on disk and update db

    - parse disk and re-insert pdf and txt files

    Directory tree structure comes from bht module, and looks like

        DATA/web-upload/
            F6114E906C3A9BA154D5BA772F661E1FC66CB974.pdf
            F6114E906C3A9BA154D5BA772F661E1FC66CB974/
            ├── 10105100046361202038319_bibheliotech_V1.txt
            ├── F6114E906C3A9BA154D5BA772F661E1FC66CB974.pdf
            └── F6114E906C3A9BA154D5BA772F661E1FC66CB974.tei.xml

    where F6114E906C3A9BA154D5BA772F661E1FC66CB974 is the paper name
    and 10105100046361202038319_bibheliotech_V1.txt the output catalog file.

    (here, it is an Istex id)

    """
    # First remove all papers
    for _p in Paper.query.all():
        db.session.delete(_p)
        db.session.commit()
    # Then
    # Search for pdf file in base directory and build corresponding Paper
    for _f in Path(current_app.config["WEB_UPLOAD_DIR"]).glob("*.pdf"):
        pdf_filename = os.path.basename(str(_f))
        paper_name = pdf_filename.split(".")[0]
        pdf_filepath = os.path.join(current_app.config["WEB_UPLOAD_DIR"], pdf_filename)
        _p = Paper(title=paper_name, pdf_path=pdf_filepath)
        # If subdirectory  exists and has txt catalog, update paper accordingly
        cat_filename = None
        paper_dir = os.path.join(current_app.config["WEB_UPLOAD_DIR"], paper_name)
        if os.path.isdir(paper_dir):
            try:
                cat_filename = str(
                    list(Path(paper_dir).glob("*bibheliotech_V1.txt"))[0]
                )
            except IndexError:
                cat_filename = None
        if cat_filename is not None:
            _p.set_cat_path(
                os.path.join(current_app.config["WEB_UPLOAD_DIR"], cat_filename)
            )

        db.session.add(_p)
        db.session.commit()

    papers = Paper.query.all()
    print(f"Updated {len(papers)} papers")


@cli.command("mock_papers")
def mock_papers():
    """Create a false list of papers inserted in database for test purpose"""
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


@cli.command("list_events")
@click.argument("mission_id", required=False)
def list_events(mission_id=None):
    """Show all events contained in database"""
    if mission_id:
        events = HpEvent.query.filter_by(mission_id=mission_id)
    else:
        events = HpEvent.query.all()
    for e in events:
        print(e)


@cli.command("refresh_events")
def refresh_events():
    """Reparse catalogs txt files

    \b
    - delete events
    - read

    Can be used in conjunction with refresh_papers() that has to be run first.

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

    events = HpEvent.query.all()
    papers = Paper.query.all()
    print(f"Updated {len(events)} events from {len(papers)} papers")


@cli.command("feed_catalog")
@click.argument("catalog_file")
def feed_catalog(catalog_file):
    """From a catalog file, feed db with events"""
    catfile_to_db(catalog_file)


if __name__ == "__main__":
    cli()
