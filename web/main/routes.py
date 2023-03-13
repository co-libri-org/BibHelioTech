import datetime
import json
import os
import re

import redis
import requests
import filetype

from requests import RequestException
from rq import Queue
from rq.exceptions import NoSuchJobError
from rq.job import Job

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
from web.models import Paper, Mission, HpEvent, rows_to_catstring
from web.bht_proxy import get_pipe_callback
from web.errors import PdfFileError
from web.istex_proxy import istex_url_to_json, istex_id_to_url


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


def get_paper_file(paper_id, file_type):
    file_path = None
    paper = db.session.get(Paper, paper_id)
    if paper is None:
        flash(f"No such paper {paper_id}")
        return None

    if file_type == "pdf" and paper.has_pdf:
        file_path = paper.pdf_path
    elif file_type == "cat" and paper.has_cat:
        file_path = paper.cat_path

    if file_path is None:
        flash(f"No {file_type} file for paper {paper_id}")
        return None

    if not os.path.isabs(file_path):
        file_path = os.path.join(current_app.config["WEB_UPLOAD_DIR"], file_path)

    if not os.path.isfile(file_path):
        flash(f"No {file_type} file for paper {paper_id}")
        return None

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
        raise e
    return r.content, filename


def pdf_to_db(file_stream, filename):
    """Push Paper to db from a pdf stream

    Update Paper's pdf content if exists

    :parameter: file_stream the file content
    :parameter: filename
    :return: the paper's id
    """
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
    paper = Paper.query.filter_by(title=paper_title).one_or_none()
    if paper is None:
        paper = Paper(title=paper_title, pdf_path=_file_path)
    else:
        paper.pdf_path = _file_path
    db.session.add(paper)
    db.session.commit()
    return paper.id


@bp.app_template_filter("staticversion")
def staticversion_filter(filename):
    newfilename = "{0}?v={1}".format(filename, current_app.config["VERSION"])
    return newfilename


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


@bp.route("/paper/del/<paper_id>", methods=["GET"])
def paper_del(paper_id):
    paper = db.session.get(Paper, paper_id)
    if paper is None:
        flash(f"No such paper {paper_id}")
        return redirect(url_for("main.papers"))
    if paper.has_cat:
        os.remove(paper.cat_path)
    if paper.has_pdf:
        os.remove(paper.pdf_path)
    db.session.delete(paper)
    db.session.commit()
    flash(f"Paper {paper_id} deleted")
    return redirect(url_for("main.papers"))


@bp.route("/papers/<name>")
@bp.route("/papers")
def papers(name=None):
    if not name:
        # get all uploaded pdf stored in db
        papers_list = db.session.query(Paper).all()
        return render_template("papers.html", papers_list=papers_list)
    else:
        flash("Uploaded " + name)
        return redirect(url_for("main.papers"))


@bp.route("/upload_from_url", methods=["POST"])
def upload_from_url():
    # TODO: refactor merge with istex_upload_id()
    pdf_url = request.form.get("pdf_url")
    if pdf_url is None:
        return Response(
            "No valid parameters for url",
            status=400,
        )
    else:
        fp, filename = get_file_from_url(pdf_url)
        pdf_to_db(fp, filename)
        return redirect(url_for("main.papers"))


@bp.route("/istex_upload_id", methods=["POST"])
def istex_upload_id():
    istex_id = request.json.get("istex_id")
    if istex_id is None:
        return Response(
            "No valid parameters for url",
            status=400,
        )
    else:
        fp, filename = get_file_from_url(istex_id_to_url(istex_id))
        filename = istex_id + ".pdf"
        paper_id = pdf_to_db(fp, filename)
        return jsonify({"success": "true", "paper_id": paper_id}), 201


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
        pdf_to_db(file.read(), file.filename)
        flash(f"Uploaded {file.filename}")
        return redirect(url_for("main.papers"))


@bp.route("/bht_status/<paper_id>", methods=["GET"])
def bht_status(paper_id):
    paper = db.session.get(Paper, paper_id)
    if paper is None:
        flash(f"No such paper {paper_id}")
        return redirect(url_for("main.papers"))
    task_id = paper.task_id
    try:
        job = Job.fetch(
            task_id, connection=redis.from_url(current_app.config["REDIS_URL"])
        )
    except NoSuchJobError:
        job = None

    if job:
        from datetime import datetime

        task_started = job.started_at
        task_result = job.return_value()
        task_status = job.get_status(refresh=True)
        elapsed = ""
        if task_status == "started":
            elapsed = str(datetime.utcnow() - task_started).split(".")[0]
        elif task_status == "finished":
            elapsed = str(job.ended_at - task_started).split(".")[0]
        response_object = {
            "status": "success",
            "data": {
                "task_id": task_id,
                "task_status": task_status,
                "task_result": task_result,
                "task_elapsed": elapsed,
                "task_started": task_started,
                "paper_id": paper.id,
            },
        }
    else:
        response_object = {"status": "error"}
    return jsonify(response_object)


@bp.route("/bht_run", methods=["POST"])
def bht_run():
    paper_id = request.form["paper_id"]
    found_pdf_file = get_paper_file(paper_id, "pdf")
    if found_pdf_file is None:
        flash("No file for that paper.")
        return redirect(url_for("main.papers"))
    q = Queue(connection=redis.from_url(current_app.config["REDIS_URL"]))
    task = q.enqueue(
        get_pipe_callback(test=current_app.config["TESTING"]),
        args=(paper_id, current_app.config["WEB_UPLOAD_DIR"]),
        job_timeout=600,
    )

    paper = db.session.get(Paper, paper_id)
    paper.set_task_id(task.get_id())

    response_object = {
        "status": "success",
        "data": {"task_id": task.get_id(), "paper_id": paper.id},
    }
    return jsonify(response_object), 202


@bp.route("/istex_test", methods=["GET"])
def istex_test():
    # TODO: merge with istex/ route, and apply same thing as with get_pipe_callback()
    from web.istex_proxy import istex_json_to_json

    with open(
        os.path.join(current_app.config["BHT_DATA_DIR"], "api.istex.fr.json")
    ) as fp:
        istex_list = istex_json_to_json(json.load(fp))
    return render_template("istex.html", istex_list=istex_list)


@bp.route("/istex", methods=["GET", "POST"])
def istex():
    if request.method == "GET":
        return render_template("istex.html", istex_list=[])
    elif request.method == "POST":
        istex_req_url = request.form["istex_req_url"]
        istex_list = istex_url_to_json(istex_req_url)
        return render_template(
            "istex.html", istex_list=istex_list, istex_req_url=istex_req_url
        )
        # return render_template("istex.html", istex_list=istex_list)


@bp.route("/istex_from_url", methods=["POST"])
def istex_from_url():
    """
    Given an istex api url (found in the form request)
    Parse the json response data
    Redirect to istex main page to display papers list
    """
    istex_req_url = request.form["istex_req_url"]
    istex_list = istex_url_to_json(istex_req_url)
    return redirect(url_for("main.istex", istex_list=istex_list))


@bp.route("/catalogs", methods=["GET"])
def catalogs():
    """UI page to retrieve catalogs by mission"""
    # rebuild all missions as dict, keeping only what we need
    _missions = [
        {"name": _m.name, "id": _m.id, "num_events": len(_m.hp_events)}
        for _m in db.session.query(Mission).order_by(Mission.name).all()
        if len(_m.hp_events) > 0
    ]
    # build a list of papers with catalogs not already inserted in db
    _catalogs = [
        paper for paper in Paper.query.filter_by(cat_in_db=False).all() if paper.has_cat
    ]
    return render_template("catalogs.html", missions=_missions, catalogs=_catalogs)


@bp.route("/api/catalogs", methods=["GET"])
def api_catalogs():
    """Get the events list for a given mission
    :parameter: mission_id  in get request
    :return: list of events as dict
    """
    mission_id = request.args.get("mission_id")
    mission = Mission.query.get(mission_id)
    # TODO: extract to method and merge common code
    events_list = [
        event.get_dict()
        for event in HpEvent.query.filter_by(mission_id=mission_id).order_by(
            HpEvent.start_date
        )
    ]
    response_object = {
        "status": "success",
        "data": {
            "events": events_list,
            "mission": {
                "id": mission.id,
                "name": mission.name,
                "num_events": len(mission.hp_events),
            },
        },
    }
    return jsonify(response_object)


@bp.route("/api/catalogs/txt", methods=["GET"])
def api_catalogs_txt():
    """Download the txt version of the catalog for the mission

    :parameter: mission_id  in get request
    :return: catalog text file as attachment
    """
    mission_id = request.args.get("mission_id")
    mission = db.session.get(Mission, mission_id) if mission_id else None
    if mission_id is None or mission is None:
        return Response(
            f"No valid parameters for url: {mission_id} {mission}",
            status=400,
        )
    # TODO: extract to method and merge common code
    events_list = [
        event.get_dict()
        for event in HpEvent.query.filter_by(mission_id=mission_id).order_by(
            HpEvent.start_date
        )
    ]
    catalog_txt_stream = rows_to_catstring(events_list, mission.name)
    date_now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bht_version = current_app.config["BHT_VERSION"]
    file_name = f"{mission.name}_{date_now}_bibheliotech_V{bht_version}.txt"
    upload_dir = current_app.config["WEB_UPLOAD_DIR"]
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    file_path = os.path.join(upload_dir, file_name)
    with open(file_path, "w") as fd:
        fd.write(catalog_txt_stream)
        fd.close()
    return send_file(file_path, as_attachment=True, download_name=file_name)


@bp.route("/api/push_catalog", methods=["POST"])
def api_push_catalog():
    """Inserts hp_events to db from paper's  catalog

    :argument: paper_id in POST request as json
    :method: GET
    :return: json result
    """
    paper_id = request.json.get("paper_id")
    paper = db.session.get(Paper, paper_id)
    paper.push_cat()
    response_object = {"status": "success", "data": {"paper_id": paper_id}}
    return jsonify(response_object), 201
