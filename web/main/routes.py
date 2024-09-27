import datetime
import json
import os

import dateutil.parser as parser
import redis
import filetype
import requests

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

from bht.errors import BhtCsvError
from tools import StepLighter
from . import bp
from web import db
from web.models import Paper, Mission, HpEvent, BhtFileType, Doi
from bht.catalog_tools import rows_to_catstring
from web.bht_proxy import get_pipe_callback
from web.istex_proxy import (
    get_file_from_url,
    get_file_from_id,
    json_to_hits,
    IstexDoctype,
    ark_to_istex_url,
)
from ..errors import IstexError, WebError


class StatusResponse:
    """
    In response to a get_status api request,
    instantiate an object with arguments,
    then return the jsonified dictionnary as expected by the request
    """

    def __init__(
        self,
        status: str = "success",
        paper_id: int = None,
        ppl_ver: str = None,
        task_status: str = None,
        task_started: datetime = None,
        cat_is_processed: bool = None,
        message: str = None,
        alt_message: str = None,
    ):
        self.status = status
        self.paper_id = paper_id
        self.ppl_ver = ppl_ver
        self.task_status = task_status
        self.task_started = task_started
        self.cat_is_processed = cat_is_processed
        self.message = message
        self.alt_message = alt_message
        if task_started is not None:
            task_started_str = task_started.strftime("%a, %b %d, %Y - %H:%M:%S")
        else:
            task_started_str = "(no time info)"

        if task_status in ["started", "finished", "failed"] and alt_message is None:
            self.alt_message = f"Started {task_started_str}"
        elif task_status in ["queued"] and alt_message is None:
            self.alt_message = f"Waiting since {task_started_str}"

    @property
    def _response(self):
        return {
            "status": self.status,
            "data": {
                "paper_id": self.paper_id,
                "ppl_ver": self.ppl_ver,
                "task_status": self.task_status,
                "cat_is_processed": self.cat_is_processed,
                "message": self.message,
                "alt_message": self.alt_message,
            },
        }

    @property
    def json(self):
        return jsonify(self._response)

    def set_ppl_ver(self, ppl_ver):
        self.ppl_ver = ppl_ver


def allowed_file(filename):
    # TODO: REFACTOR use models.FileType instead
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


# TODO: REFACTOR please move function to models.paper.method
def get_paper_file(paper_id, file_type):
    """
    Return the filepath for the given paper as id

    @param paper_id:  id of the paper
    @param file_type:  type of the wanted file (@see FileType)
    @return:
    """

    paper = db.session.get(Paper, paper_id)
    if paper is None:
        flash(f"No such paper {paper_id}")
        return None

    # TODO: REWRITE
    # check filetype
    if isinstance(file_type, str):
        # convert to enum
        try:
            file_type = getattr(BhtFileType, file_type.upper())
        except AttributeError:
            flash(f"Wrong file type {file_type}")
            return None
    elif not isinstance(file_type, BhtFileType):
        flash(f"Wrong file type {file_type}")
        return None

    # TODO: REWRITE
    if file_type == BhtFileType.PDF and paper.has_pdf:
        file_path = paper.pdf_path
    elif file_type == BhtFileType.CAT and paper.has_cat:
        file_path = paper.cat_path
    elif file_type == BhtFileType.TXT and paper.has_txt:
        file_path = paper.txt_path
    else:
        flash(f"No {file_type} file for paper {paper_id}")
        return None

    if not os.path.isabs(file_path):
        file_path = os.path.join(current_app.config["WEB_UPLOAD_DIR"], file_path)

    if not os.path.isfile(file_path):
        flash(f"No {file_type} file for paper {paper_id}")
        return None

    return file_path


# TODO: REWRITE rename to file_to_db
# TODO: REFACTOR insert into models.Paper ?
# TODO: REWRITE raise exception or send message to calling route to be flashed
def pdf_to_db(file_stream, filename, istex_struct=None):
    """
    Push Paper to db from a pdf stream

    Update Paper's pdf content if exists

    :parameter: file_stream the file content
    :parameter: filename
    :return: the paper's id, or None if couldn't do it
    """
    filename = secure_filename(filename)
    upload_dir = current_app.config["WEB_UPLOAD_DIR"]
    if not os.path.isdir(upload_dir):
        os.makedirs(upload_dir)
    _file_path = os.path.join(upload_dir, filename)
    with open(_file_path, "wb") as _fd:
        _fd.write(file_stream)
    if not os.path.isfile(_file_path):
        return redirect(url_for("main.papers"))
    _guessed_filetype = filetype.guess(_file_path)
    _split_filename = os.path.splitext(filename)
    _file_type = None
    if _guessed_filetype and _guessed_filetype.mime == "application/pdf":
        _file_type = BhtFileType.PDF
    elif _split_filename[1] in [".cleaned", ".txt"]:
        _file_type = BhtFileType.TXT
    else:
        return None
    if istex_struct is not None:
        _paper_title = istex_struct["title"]
    else:
        _paper_title = _split_filename[0]
    paper = Paper.query.filter_by(title=_paper_title).one_or_none()
    if paper is None:
        paper = Paper(title=_paper_title)

    # set_file_path() will add and commit paper
    paper.set_file_path(_file_path, _file_type)
    if istex_struct is not None:
        paper.set_doi(istex_struct["doi"])
        paper.set_ark(istex_struct["ark"])
        paper.set_pubdate(istex_struct["pub_date"])
        paper.set_istex_id(istex_struct["istex_id"])
    return paper.id


@bp.app_template_filter("short_datetime")
def short_datetime(date_time):
    if type(date_time) is str:
        date = parser.parse(date_time)
        native = date.replace(tzinfo=None)
    else:
        native = date_time
    new_datetime = native.strftime("%Y-%m-%dT%H:%M:%S")
    return new_datetime


@bp.app_template_filter("staticversion")
def staticversion_filter(filename):
    newfilename = "{0}?v={1}".format(filename, current_app.config["VERSION"])
    return newfilename


@bp.app_template_filter("basename")
def basename_filter(filename):
    if not filename:
        return None
    return os.path.basename(filename)


@bp.route("/")
def index():
    # return render_template("index.html")
    return redirect(url_for("main.catalogs"))


@bp.route("/changelog/<module>")
@bp.route("/changelog", defaults={"module": "main"})
def changelog(module):
    import markdown

    if module == "main":
        changelog_path = os.path.join(
            current_app.config["BHT_ROOT_DIR"], "CHANGELOG.md"
        )
    elif module == "pipeline":
        changelog_path = os.path.join(
            current_app.config["BHT_ROOT_DIR"], "bht", "PIPELINE_CHANGELOG.md"
        )
    else:
        flash(f"No such log for module {module}")
        return redirect(url_for("main.papers"))

    with open(changelog_path) as changelog_file:
        changelog_html = markdown.markdown(changelog_file.read())
    return render_template("changelog.html", changelog_html=changelog_html)


@bp.route("/about")
def about():
    return render_template("about.html")


@bp.route("/configuration")
def configuration():
    return render_template("configuration.html", configuration=current_app.config)


# TODO: REFACTOR merge following 3 routes/methods
# and rewrite calls into papers.html
# and tests
@bp.route("/txt/<paper_id>")
def txt(paper_id):
    file_path: str = get_paper_file(paper_id, BhtFileType.TXT)
    if file_path is None:
        return redirect(url_for("main.papers"))
    else:
        return send_file(file_path)


@bp.route("/pdf/<paper_id>")
def pdf(paper_id):
    file_path: str = get_paper_file(paper_id, BhtFileType.PDF)
    if file_path is None:
        return redirect(url_for("main.papers"))
    else:
        return send_file(file_path)


@bp.route("/cat/<paper_id>", methods=["GET"])
def cat(paper_id):
    file_path: str = get_paper_file(paper_id, BhtFileType.CAT)
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


@bp.route("/paper/update/<paper_id>", methods=["GET"])
def paper_update(paper_id):
    paper = db.session.get(Paper, paper_id)
    try:
        paper.istex_update()
        flash("Paper updated from Istex api")
    except IstexError:
        flash(f"There was an error on update", "error")
    return redirect(url_for("main.paper_show", paper_id=paper_id))


@bp.route("/paper/show/<paper_id>", methods=["GET"])
def paper_show(paper_id):
    paper = db.session.get(Paper, paper_id)
    if paper is None:
        flash(f"No such paper {paper_id}")
        return redirect(url_for("main.papers"))
    return render_template("paper.html", paper=paper)


@bp.route(
    "/paper/<pipeline_mode>/<paper_id>/<step_num>",
    defaults={"disp_mode": "enlighted"},
    methods=["GET"],
)
@bp.route("/paper/<pipeline_mode>/<paper_id>/<step_num>/<disp_mode>", methods=["GET"])
def paper_pipeline(pipeline_mode, paper_id, step_num, disp_mode):
    if pipeline_mode not in ["sutime", "entities"]:
        flash(f"No such pipeline mode {pipeline_mode} for paper {paper_id} ")
        return redirect(url_for("main.papers"))
    if disp_mode not in ["enlighted", "raw", "analysed"]:
        flash(f"No such display mode {disp_mode} for paper {paper_id} ")
        return redirect(url_for("main.paper_show", paper_id=paper_id))
    # get the papers directory path
    paper = db.session.get(Paper, paper_id)
    if not paper:
        flash(f"No such paper {paper_id}", "error")
        return redirect(url_for("main.papers"))
    if not paper.has_cat:
        flash(f"Paper {paper_id} was not already processed.", "warning")
        return redirect(url_for("main.paper_show", paper_id=paper_id))
    ocr_dir = os.path.dirname(paper.cat_path)
    step_lighter = StepLighter(ocr_dir, step_num, pipeline_mode)

    return render_template(
        "colored_steps.html",
        paper=paper,
        curr_step=int(step_num),
        paper_id=paper_id,
        pipeline_mode=pipeline_mode,
        step_lighter=step_lighter,
        disp_mode=disp_mode,
    )


@bp.route("/enlighted_json", methods=["GET"])
def enlighted_json():
    pipeline_mode = request.args.get("pipeline_mode")
    paper_id = request.args.get("paper_id")
    step_num = request.args.get("step_num")
    comp_type = request.args.get("comp_type")
    paper = db.session.get(Paper, paper_id)
    if not paper:
        flash(f"No such paper {paper_id}")
        return redirect(url_for("main.papers"))
    if not paper.has_cat:
        flash(f"Paper {paper_id} was not already processed.", "warning")
        return redirect(url_for("main.paper_show", paper_id=paper_id))
    ocr_dir = os.path.dirname(paper.cat_path)
    step_lighter = StepLighter(ocr_dir, step_num, pipeline_mode)
    if comp_type == "raw":
        response = send_file(
            step_lighter.json_filepath,
            mimetype="application/json",
        )
    elif comp_type == "analysed":
        response = Response(
            response=step_lighter.analysed_json,
            mimetype="text/plain",
            headers={"Content-disposition": "inline"},
        )
        # headers={'Content-disposition': 'inline; filename=hello.txt'})
    else:
        flash(f"Wrong comp_type value", "warning")
        return redirect(url_for("main.paper_show", paper_id=paper_id))

    return response


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
    # TODO: REFACTOR merge with istex_upload_id()
    file_url = request.form.get("file_url")
    if file_url:
        filestream, filename = get_file_from_url(file_url)
        paper_id = pdf_to_db(filestream, filename)
        flash(f"Uploaded {filename} to paper {paper_id}")
        return redirect(url_for("main.papers"))
    else:
        return Response(
            "No valid parameters for url",
            status=400,
        )


@bp.route("/istex_upload_id", methods=["POST"])
def istex_upload_id():
    istex_id = request.json.get("istex_id")
    try:
        doc_type = IstexDoctype(request.json.get("doc_type"))
    except ValueError:
        doc_type = IstexDoctype.PDF
    if not istex_id:
        return Response(
            "No valid parameters for url",
            status=400,
        )
    else:
        fs, filename, istex_struct = get_file_from_id(istex_id, doc_type)
        paper_id = pdf_to_db(fs, filename, istex_struct)
        return (
            jsonify(
                {
                    "success": "true",
                    "istex_id": istex_id,
                    "paper_id": paper_id,
                    "filename": filename,
                }
            ),
            201,
        )


@bp.route("/upload", methods=["POST"])
def upload():
    # TODO: REWRITE to upload_from_file()
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
        return redirect(url_for("main.papers"))  #

    # TODO: REFACTOR cut and delegate to Paper and Task models
    # Get task info from db if task has finished
    if paper.task_status == "finished" or paper.task_status == "failed":
        try:
            elapsed = str(paper.task_stopped - paper.task_started).split(".")[0]
        except Exception as e:
            current_app.logger.error(f"Got error on paper task date: {e}")
            elapsed = ""
        response_object = StatusResponse(
            paper_id=paper.id,
            task_status=paper.task_status,
            task_started=paper.task_started,
            cat_is_processed=paper.has_cat and paper.cat_in_db,
            message=f"{paper.task_status} {elapsed}",
        )
    else:  # Get task info from task manager
        task_id = paper.task_id
        try:
            job = Job.fetch(
                task_id, connection=redis.from_url(current_app.config["REDIS_URL"])
            )
            task_status = job.get_status(refresh=True)

            if task_status == "started":
                task_started = job.started_at
                elapsed = str(datetime.datetime.utcnow() - task_started).split(".")[0]
            elif task_status in ["finished", "failed"]:
                task_started = job.started_at
                elapsed = str(job.ended_at - task_started).split(".")[0]
            elif task_status == "queued":
                task_started = job.enqueued_at
                elapsed = ""
            else:
                # TODO: send a response object
                raise WebError(f"Unknown status {task_status}")

            paper.set_task_status(task_status)
            paper.set_task_started(task_started)
            paper.set_task_stopped(job.ended_at)
            response_object = StatusResponse(
                paper_id=paper.id,
                task_status=task_status,
                task_started=task_started,
                cat_is_processed=paper.has_cat and paper.cat_in_db,
                message=f"{task_status} {elapsed}",
            )
        except NoSuchJobError:
            response_object = StatusResponse(
                paper_id=paper.id,
                task_status="undefined",
                message="No job run yet",
                alt_message="No pipeline was run on that paper",
            )
        except redis.connection.ConnectionError:
            response_object = StatusResponse(
                status="failed",
                paper_id=paper.id,
                message="Redis Cnx Err",
                alt_message="Database to read tasks status is unreachable",
            )
            return response_object.json, 503

        # TODO: END CUTTING
    response_object.set_ppl_ver(paper.pipeline_version)
    return response_object.json, 200


@bp.route("/bht_run", methods=["POST"])
def bht_run():
    paper_id = request.form["paper_id"]
    file_type = request.form["file_type"]
    found_file = get_paper_file(paper_id, file_type.upper())
    if found_file is None:
        flash("No file for that paper.")
        return redirect(url_for("main.papers"))

    # TODO: REFACTOR CUT START and delegate to Paper and Task models
    try:
        q = Queue(connection=redis.from_url(current_app.config["REDIS_URL"]))
        task = q.enqueue(
            get_pipe_callback(test=current_app.config["TESTING"]),
            args=(paper_id, current_app.config["WEB_UPLOAD_DIR"], file_type),
            job_timeout=600,
        )
    except redis.connection.ConnectionError:
        response_object = StatusResponse(
            status="failed",
            paper_id=int(paper_id),
            message="Failed, no Redis",
            alt_message="System to run tasks is unreachable",
        )
        return response_object.json, 503

    paper = db.session.get(Paper, paper_id)
    paper.set_task_id(task.get_id())
    paper.set_task_status("queued")
    paper.set_cat_path(None)
    # TODO: CUT END

    response_object = StatusResponse(
        status="success", task_status="queued", paper_id=paper.id
    )
    return response_object.json, 202


@bp.route("/istex_test", methods=["GET"])
def istex_test():
    # TODO: REFACTOR merge with istex/ route, and apply same thing as with get_pipe_callback()
    from web.istex_proxy import json_to_hits

    with open(
        os.path.join(current_app.config["BHT_DATA_DIR"], "api.istex.fr.json")
    ) as fp:
        istex_list = json_to_hits(json.load(fp))
    return render_template("istex.html", istex_list=istex_list)


@bp.route("/istex", methods=["GET", "POST"])
def istex():
    """
    Given an istex api url (found in the form request)
    Parse the json response data
    Redirect to our "istex" page to display papers list
    """
    # Juste display form at first sight
    if request.method == "GET":
        return render_template("istex.html", istex_list=[])

    # else method == "POST", deal with url or ark arguments
    istex_req_url = request.form["istex_req_url"]
    ark_istex = request.form["ark_istex"]
    if istex_req_url:
        # just go on with it
        pass
    elif ark_istex:
        # then build the request_url from ark
        istex_req_url = ark_to_istex_url(ark_istex)
    else:
        flash(f"Could not read any argument: istex_req_url or ark_istex ", "error")
        return redirect(url_for("main.istex"))

    # build a link to allow direct human check by click into error message
    istex_req_url_a = f'<a target="_blank" href="{istex_req_url}" title="get istex request"> {istex_req_url} </a>'

    # now try to get some results from Istex, or quit with err message
    try:
        r = requests.get(url=istex_req_url)
        json_content = r.json()
        istex_list = json_to_hits(json_content)
    except (
        requests.exceptions.MissingSchema,
        requests.exceptions.InvalidURL,
        requests.exceptions.ConnectionError,
    ):
        flash(f"Could not connect to <{istex_req_url}>", "error")
        return redirect(url_for("main.istex"))
    except requests.exceptions.JSONDecodeError:
        flash(f"Wrong JSON content from <{istex_req_url_a}>", "error")
        return redirect(url_for("main.istex"))
    except Exception as e:
        flash(f"There was an error reading json from <{istex_req_url_a}>", "error")
        flash(f"{e.__repr__()}", "error")
        return redirect(url_for("main.istex"))

    # get papers from db, so we can show we already have them
    istex_papers = {p.istex_id: p for p in Paper.query.all()}

    # build dict of papers indexed with istex_id
    return render_template(
        "istex.html",
        istex_list=istex_list,
        istex_req_url=istex_req_url,
        istex_papers=istex_papers,
    )


# TODO: merge /events and /catalogs routes
@bp.route("/events", defaults={"ref_id": None, "ref_name": None}, methods=["GET"])
@bp.route("/events/<ref_name>/<ref_id>", methods=["GET"])
def events(ref_name, ref_id):
    """UI page to display events by paper or mission, or any other criteria"""
    paper = None
    found_events = []
    all_events = HpEvent.query.all()
    if ref_name is None:
        found_events = all_events
    elif ref_name == "paper":
        paper = Paper.query.get(ref_id)
        found_events = paper.get_events()

    # translate events to dict list
    events_dict_list = [_e.get_dict() for _e in found_events]

    return render_template("events.html", events=events_dict_list, paper=paper)


@bp.route("/admin", methods=["GET"])
def admin():

    # build a list of papers with catalogs not already inserted in db
    _catalogs = [
        paper for paper in Paper.query.filter_by(cat_in_db=False).all() if paper.has_cat
    ]

    return render_template("admin.html", catalogs=_catalogs)


@bp.route("/catalogs", methods=["GET"])
def catalogs():
    """UI page to retrieve catalogs by mission"""

    # rebuild all missions as dict, keeping only what we need
    _missions = [
        {"name": _m.name, "id": _m.id, "num_events": len(_m.hp_events)}
        for _m in db.session.query(Mission).order_by(Mission.name).all()
        if len(_m.hp_events) > 0
    ]

    # now get some stats and pack as dict
    processed_papers = Paper.query.filter_by(cat_in_db=True).all()
    all_missions = Mission.query.all()
    all_events = HpEvent.query.all()
    if len(all_events) > 1:
        events_start_dates_asc = sorted(
            [_e.start_date for _e in all_events], reverse=False
        )
        events_stop_dates_dsc = sorted(
            [_e.stop_date for _e in all_events], reverse=True
        )
        global_start = events_start_dates_asc[0].strftime("%Y-%m-%d")
        global_stop = events_stop_dates_dsc[0].strftime("%Y-%m-%d")
    else:
        global_start = ""
        global_stop = ""

    _db_stats = {
        "num_events": len(all_events),
        "num_papers": len(processed_papers),
        "num_missions": len(all_missions),
        "global_start": global_start,
        "global_stop": global_stop,
    }
    return render_template("catalogs.html", missions=_missions, db_stats=_db_stats)


@bp.route("/api/catalogs", methods=["GET"])
def api_catalogs():
    """Get the events list for a given mission
    :parameter: mission_id  in get request
    :return: list of events as dict
    """
    mission_id = request.args.get("mission_id")
    mission = Mission.query.get(mission_id)
    # TODO: REFACTOR extract to event model method and merge common code with api_catalog_txt
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
    """Download the txt version of the catalog for the given mission

    To do that,
     - retrieve from db all events related to that mission id
     - Dump this events list to a text file.


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
    # TODO: REFACTOR extract to method and merge common code with api_catalogs
    events_list = [
        event.get_dict()
        for event in HpEvent.query.filter_by(mission_id=mission_id).order_by(
            HpEvent.start_date
        )
    ]
    catalog_txt_stream = rows_to_catstring(events_list, mission.name)
    date_now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bht_pipeline_version = current_app.config["BHT_PIPELINE_VERSION"]
    # TODO: build catalog name else where, may be from some bht.method()
    file_name = f"{mission.name}_{date_now}_bibheliotech_V{bht_pipeline_version}.txt"
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
    try:
        paper.push_cat()
        response_object = {"status": "success", "data": {"paper_id": paper_id}}
        flash(f"Added catalog for paper {paper_id}")
    except BhtCsvError as e:
        response_object = {
            "status": "error",
            "data": {"paper_id": paper_id, "error_msg": e.message},
        }
        flash(f"Error trying to add catalog for {paper_id}", "error")
    return jsonify(response_object), 201
