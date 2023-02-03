import redis
from rq import Connection, Worker
from flask.cli import FlaskGroup
from web import create_app, db
from web.models import Paper

app = create_app()
cli = FlaskGroup(create_app=create_app)


@cli.command("create_db")
def create_db():
    db.create_all()


@cli.command("add_paper")
def add_paper():
    paper = Paper(title="This is my first title",
                  pdf_path="/this/is/my/file.pdf",
                  cat_path="/this/is/my/cat.txt",
                  task_id=""
                  )
    db.session.add(paper)
    db.session.commit()


@cli.command("list_papers")
def list_papers():
    print(Paper.query.all())


@cli.command("run_worker")
def run_worker():
    redis_url = app.config["REDIS_URL"]
    redis_connection = redis.from_url(redis_url)
    with Connection(redis_connection):
        worker = Worker(app.config["QUEUES"])
        worker.work()


if __name__ == "__main__":
    cli()
