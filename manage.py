import redis
from flask import current_app
from rq import Connection, Worker
from flask.cli import FlaskGroup
from web import create_app, db
from web.models import Paper

cli = FlaskGroup(create_app=create_app)


@cli.command("show_config")
def show_config():
    from pprint import pprint
    pprint(current_app.config)
    print(db.engine)


@cli.command("create_db")
def create_db():
    db.create_all()


@cli.command("mock_papers")
def mock_papers():
    papers_list = [["aa33199-18", "aa33199-18.pdf", None, None],
                   ["2016GL069787", "2016GL069787.pdf",
                    "2016GL069787/1010022016gl069787_bibheliotech_V1.txt", None],
                   ["5.0067370", "5.0067370.pdf", "5.0067370/10106350067370_bibheliotech_V1.txt", None]]
    for p_l in papers_list:
        paper = Paper(title=p_l[0],
                      pdf_path=p_l[1],
                      cat_path=p_l[2],
                      task_id=p_l[3]
                      )
        db.session.add(paper)
    db.session.commit()


@cli.command("list_papers")
def list_papers():
    for p in Paper.query.all():
        print(p)


@cli.command("run_worker")
def run_worker():
    redis_url = current_app.config["REDIS_URL"]
    redis_connection = redis.from_url(redis_url)
    with Connection(redis_connection):
        worker = Worker(current_app.config["QUEUES"])
        worker.work()


if __name__ == "__main__":
    cli()
