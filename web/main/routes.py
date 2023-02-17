import glob
import os
import re

import redis
import requests
import filetype

from requests import RequestException
from rq import Connection, Queue

from werkzeug.utils import secure_filename

from flask import (
    render_template,
    current_app,
    request,
    flash,
    redirect,
    url_for,
    send_file,
    jsonify,
    Response,
)

from . import bp
from web import db
from web.models import Paper
from web.bht_proxy import runfile_and_updatedb
from web.errors import PdfFileError
from web.istex_proxy import istex_url_to_json


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


def get_paper_file(paper_id, file_type):
    file_path = None
    paper = Paper.query.get(paper_id)
    if paper is None:
        flash(f"No such paper {paper_id}")
        return None

    if file_type == "pdf":
        file_path = paper.pdf_path
    elif file_type == "cat":
        file_path = paper.cat_path

    if file_path is None:
        flash(f"No {file_type} file for paper {paper_id}")
        return None

    if not os.path.isabs(file_path):
        file_path = os.path.join(current_app.config["WEB_UPLOAD_DIR"], file_path)

    return file_path


def get_file_from_url(url):
    r = requests.get(url)
    if not r.headers["Content-Type"] == "application/pdf":
        raise PdfFileError("No pdf in url")
    try:
        with requests.get(url) as r:
            if "Content-Disposition" in r.headers.keys():
                filename = re.findall(
                    "filename=(.+)", r.headers["Content-Disposition"]
                )[0]
            else:
                filename = url.split("/")[-1]
    except RequestException as e:
        raise (e)
    return r.content, filename


def save_to_db(file_stream, filename):
    filename = secure_filename(filename)
    upload_dir = current_app.config["WEB_UPLOAD_DIR"]
    if not os.path.isdir(upload_dir):
        os.makedirs(upload_dir)
    _file_path = os.path.join(upload_dir, filename)
    with open(_file_path, "wb") as _fd:
        _fd.write(file_stream)
    if not os.path.isfile(_file_path):
        raise PdfFileError(f"no such file: {_file_path}")
    if not filetype.guess(_file_path).mime == "application/pdf":
        raise Exception(f"{_file_path} is not pdf ")
    paper_title = filename.replace(".pdf", "")
    paper = Paper(title=paper_title, pdf_path=_file_path)
    db.session.add(paper)
    db.session.commit()
    return paper.id


@bp.route("/")
def index():
    # return render_template("index.html")
    return redirect(url_for("main.papers"))


@bp.route("/about")
def about():
    return render_template("about.html")


@bp.route("/configuration")
def configuration():
    return render_template("configuration.html", configuration=current_app.config)


@bp.route("/pdf/<paper_id>")
def pdf(paper_id):
    file_path = get_paper_file(paper_id, "pdf")
    if file_path is None:
        return redirect(url_for("main.papers"))
    else:
        return send_file(file_path)


@bp.route("/cat/<paper_id>", methods=["GET"])
def cat(paper_id):
    file_path = get_paper_file(paper_id, "cat")
    if file_path is None:
        return redirect(url_for("main.papers"))
    else:
        return send_file(file_path)


@bp.route("/papers/<name>")
@bp.route("/papers")
def papers(name=None):
    if not name:
        # get all uploaded pdf stored in db
        papers_list = Paper.query.all()
        return render_template("papers.html", papers_list=papers_list)
    else:
        flash("Uploaded " + name)
        return redirect(url_for("main.papers"))


@bp.route("/upload_from_url", methods=["POST"])
def upload_from_url():
    pdf_url = request.form.get("pdf_url")
    if pdf_url is None:
        return Response(
            "No valid parameters for url",
            status=400,
        )
    else:
        fp, filename = get_file_from_url(pdf_url)
        save_to_db(fp, filename)
        return redirect(url_for("main.papers"))


@bp.route("/upload", methods=["POST"])
def upload():
    # check if the post request has the file part
    if "file" not in request.files:
        flash("No file part")
        return redirect(url_for("main.papers"))
    file = request.files["file"]
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == "":
        flash("No selected file")
        return redirect(url_for("main.papers"))
    if file and allowed_file(file.filename):
        save_to_db(file.stream, file.filename)
        flash(f"Uploaded {file.filename}")
        return redirect(url_for("main.papers"))


@bp.route("/bht_run", methods=["POST"])
def bht_run():
    paper_id = request.form["paper_id"]
    found_pdf_file = get_paper_file(paper_id, "pdf")
    if found_pdf_file is None:
        return redirect(url_for("main.papers"))
    with Connection(redis.from_url(current_app.config["REDIS_URL"])):
        q = Queue()
        task = q.enqueue(
            runfile_and_updatedb,
            args=(paper_id, found_pdf_file, current_app.config["WEB_UPLOAD_DIR"]),
            job_timeout=600,
        )

    paper = Paper.query.get(paper_id)
    paper.set_task_id(task.get_id())

    response_object = {
        "status": "success",
        "data": {"task_id": task.get_id(), "paper_id": paper.id},
    }
    return jsonify(response_object), 202


@bp.route("/istex", methods=["GET", "POST"])
def istex():
    if request.method == "GET":
        return render_template("istex.html", istex_list=[])
    elif request.method == "POST":
        istex_req_url = request.form["istex_req_url"]
        istex_list = istex_url_to_json(istex_req_url)
        return render_template("istex.html", istex_list=istex_list)


@bp.route("/istex_from_url", methods=["POST"])
def istex_from_url():
    istex_req_url = request.form["istex_req_url"]
    istex_list = istex_url_to_json(istex_req_url)
    return redirect(url_for("main.istex", istex_list=istex_list))


@bp.route("/bht_status/<paper_id>", methods=["GET"])
def bht_status(paper_id):
    paper = Paper.query.get(paper_id)
    if paper is None:
        flash(f"No such paper {paper_id}")
        return redirect(url_for("main.papers"))
    task_id = paper.task_id
    with Connection(redis.from_url(current_app.config["REDIS_URL"])):
        q = Queue()
        task = q.fetch_job(task_id)
    if task:
        response_object = {
            "status": "success",
            "data": {
                "task_id": task.get_id(),
                "task_status": task.get_status(),
                "task_result": task.result,
                "paper_id": paper.id,
            },
        }
    else:
        response_object = {"status": "error"}
    return jsonify(response_object)


@bp.route("/catalogs", methods=["GET"])
def catalogs():
    _catalogs = glob.glob(
        os.path.join(current_app.config["BHT_PAPERS_DIR"], "**", "*bibhelio*.txt"),
        recursive=True,
    )
    return render_template("catalogs.html", catalogs=_catalogs)
