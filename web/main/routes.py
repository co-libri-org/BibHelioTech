import json
import os
from zoneinfo import ZoneInfo

import dateutil.parser as parser
import pandas as pd
import redis
import requests

from rq import Queue
from rq.exceptions import NoSuchJobError
from rq.job import Job

from sqlalchemy import func

from flask import (
    render_template,
    current_app,
    request,
    flash,
    redirect,
    url_for,
    send_file,
    Response,
    send_from_directory,
)

from bht.errors import BhtCsvError
from bht.pipeline import PipeStep
from tools import StepLighter
from . import bp
from web import db
from web.models import Paper, Mission, HpEvent, BhtFileType, istexid_to_paper, file_to_db
from bht.catalog_tools import rows_to_catstring
from web.bht_proxy import get_pipe_callback
from web.istex_proxy import (
    get_file_from_url,
    get_file_from_id,
    json_to_hits,
    IstexDoctype,
    ark_to_istex_url,
)
from ..errors import IstexError, WebError, FilePathError

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from flask import jsonify


@dataclass
class StatusResponse:
    """Handles status response formatting for API requests"""

    VALID_STATUSES = {"queued", "started", "finished", "failed"}

    status: str
    http_code: int = 200
    paper: Optional['Paper'] = None
    paper_id: Optional[int] = None
    ppl_ver: Optional[str] = None
    task_status: Optional[str] = None
    cat_is_processed: Optional[bool] = False
    message: str = ""
    alt_message: str = ""

    def __post_init__(self):
        if self.status not in ["success", "failed"]:
            raise ValueError(f"response status must be failed or success, not {self.status}")

        if not (self.paper or self.paper_id):
            raise ValueError("paper_id must be provided if paper is None")

        # set fields from paper if not set by constructor
        if self.paper is not None:
            self.paper_id = self.paper_id or self.paper.id
            self.ppl_ver = self.ppl_ver or self.paper.pipeline_version
            self.task_status = self.task_status or self.paper.task_status
            self.task_started = self.paper.task_started
            self.task_stopped = self.paper.task_stopped
            self.cat_is_processed = self.paper.has_cat and self.paper.cat_in_db

        if isinstance(self.task_started, datetime):
            self.task_started = self.task_started.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("Europe/Paris"))
        if isinstance(self.task_stopped, datetime):
            self.task_stopped = self.task_stopped.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("Europe/Paris"))

    def _format_task_status(self) -> str:
        return self.task_status if self.task_status in self.VALID_STATUSES else "undefined"

    def _calculate_elapsed_time(self) -> str:
        if not isinstance(self.task_started, datetime):
            return ""

        _current_time = datetime.now(ZoneInfo("Europe/Paris"))
        if self.task_status in ["started", "queued"]:
            elapsed = _current_time - self.task_started

        elif self.task_status in ["finished", "failed"] and isinstance(self.task_stopped, datetime):
            elapsed = self.task_stopped - self.task_started
        else:
            return ""

        return str(elapsed).split(".")[0]

    def _format_message(self) -> str:
        if self.message:
            return self.message

        if self._format_task_status() == "undefined":
            return "No job run yet"

        return f"{self.task_status:9} {self._calculate_elapsed_time()}"

    def _format_alt_message(self) -> str:
        if self.alt_message:
            return self.alt_message

        started_str = self.task_started.strftime('%Y-%m-%dT%H:%M:%S') if self.task_started else "(no time info)"

        if self.task_status in ["started", "finished", "failed"]:
            return f"Started {started_str}"
        elif self.task_status == "queued":
            return f"Waiting since {started_str}"

        return ""

    @property
    def response(self):
        data = {
            "paper_id": self.paper_id,
            "ppl_ver": self.ppl_ver,
            "task_status": self._format_task_status(),
            "task_started": self.task_started,
            "task_stopped": self.task_stopped,
            "cat_is_processed": self.cat_is_processed,
            "message": self._format_message(),
            "alt_message": self._format_alt_message()
        }
        return jsonify({"status": self.status, "data": data}), self.http_code


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


#  - - - - - - - - - - - - - - - - - - A P P  C O N F I G U R A T I O N S - - - - - - - - - - - - - - - - - - - - #

@bp.app_template_filter("short_timedelta")
def short_timedelta(in_timedelta):
    # out_timedelta = ""
    # if type(in_timedelta) is np.timedelta64:
    #     out_timedelta = in_timedelta.astype(str)[:-6]
    # elif type(in_timedelta) is datetime.timedelta:
    #     out_timedelta = datetime.timedelta(
    #         days=in_timedelta.days,
    #         seconds=in_timedelta.seconds,
    #         microseconds=0,
    #     )
    out_timedelta = type(in_timedelta)

    return out_timedelta


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


# Add colors as default variable for all template
@bp.before_request
def add_css_colors_to_templates():
    # Mettre CSS_COLORS dans le contexte global des templates
    current_app.jinja_env.globals['css_colors'] = current_app.config['CSS_COLORS']


#  - - - - - - - - - - - - - - - - - - - - R O U T E S - - - - - - - - - - - - - - - - - - - - - - - - #

@bp.route("/")
def index():
    # return render_template("index.html")
    return redirect(url_for("main.catalogs"))


@bp.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(current_app.static_folder, "img"),
        "bht2-32x32.png",
        mimetype="image/vnd.microsoft.icon",
    )


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


@bp.route("/papers")
def papers():
    requested_status = request.args.get('requested_status', None)

    if requested_status not in ["queued", "started", "finished", "failed", "undefined", None]:
        flash(f"Status {requested_status} is not valid", "warning")
        return redirect(url_for("main.papers"))

    # make some statistics by pipeline job status
    state_counts = db.session.query(Paper.task_status, func.count(Paper.id)).group_by(Paper.task_status).all()

    # Add the 'undefined' state
    valid_states = ['finished', 'queued', 'started', 'failed']
    state_dict = {state: count for state, count in state_counts if state in valid_states}
    undefined_count = sum(count for state, count in state_counts if state not in valid_states)
    state_dict['undefined'] = undefined_count
    for state in valid_states:
        if state in state_dict.keys():
            continue
        state_dict[state] = 0

    # Transform to a list of dicts
    state_stats = [{'status': k, 'tag': k, 'value': state_dict[k]} for k in valid_states]
    state_stats.append({'status': 'undefined', 'tag': 'not run', 'value': state_dict['undefined']})

    # get all uploaded pdf stored in db
    # papers_list = db.session.query(Paper).all()
    page = request.args.get('page', 1, type=int)
    if requested_status is not None:
        _query = Paper.query.filter_by(task_status=requested_status)
    else:
        _query = Paper.query
    _papers = _query.paginate(
        page=page,
        per_page=current_app.config["PER_PAGE"],
        error_out=False
    )
    return render_template("papers.html", papers=_papers, state_stats=state_stats, requested_status=requested_status)


@bp.route("/upload_from_url", methods=["POST"])
def upload_from_url():
    # TODO: REFACTOR merge with istex_upload_id()
    file_url = request.form.get("file_url")
    if file_url is None:
        return Response(
            "No valid parameters for url",
            status=400,
        )
    filestream, filename = get_file_from_url(file_url)
    try:
        paper_id = file_to_db(filestream, filename, upload_dir=current_app.config["WEB_UPLOAD_DIR"])
    except FilePathError:
        flash(f"Error adding {filename} to db", "error")
    else:
        flash(f"Uploaded {filename} to paper {paper_id}")
    return redirect(url_for("main.papers"))


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
    fs, filename, istex_struct = get_file_from_id(istex_id, doc_type)
    try:
        paper_id = file_to_db(fs, filename, current_app.config["WEB_UPLOAD_DIR"], istex_struct)
    except FilePathError:
        return Response(
            f"There was an error on {filename} copy",
            status=400,
        )
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
    elif file and allowed_file(file.filename):
        try:
            file_to_db(file.read(), file.filename, upload_dir=current_app.config["WEB_UPLOAD_DIR"])
        except FilePathError:
            flash(f"Error adding {file.filename} to db", "error")
        else:
            flash(f"Uploaded {file.filename}")
    else:
        flash(f"{file.filename} Not allowed")
    return redirect(url_for("main.papers"))


@bp.route("/bht_status/<paper_id>", methods=["GET"])
def bht_status(paper_id):
    paper = db.session.get(Paper, paper_id)
    if paper is None:
        response_object = StatusResponse(paper_id=paper_id,
                                         message=f"No such paper {paper_id}",
                                         alt_message=f"No such paper {paper_id}",
                                         status="failed",
                                         http_code=404)


    # Get task info from db
    elif paper.task_status in ["finished", "failed", None]:
        response_object = StatusResponse(paper=paper,
                                         status="success",
                                         http_code=200)
    # Or Get task info from task manager
    else:
        # task_status is in ["queued", "started"] but can change before next if

        task_id = paper.task_id
        try:
            job = Job.fetch(
                task_id, connection=redis.from_url(current_app.config["REDIS_URL"])
            )
            task_status = job.get_status(refresh=True).value

            # even if we entered that case with status in ["queued", "started"] it can have changed in the mean time
            # so we need to also test  "finished" and "failed" statuses
            if task_status in ["started", "finished", "failed"]:
                task_started = job.started_at
            elif task_status == "queued":
                task_started = job.enqueued_at
            else:
                # TODO
                raise WebError(f"Unmanaged task status >>{task_status}<<")

            # Update paper's info in db
            paper.set_task_status(task_status)
            paper.set_task_started(task_started)
            paper.set_task_stopped(job.ended_at)
            response_object = StatusResponse(paper=paper,
                                             status="success",
                                             http_code=200)
        except NoSuchJobError:
            response_object = StatusResponse(paper=paper,
                                             message="Job Id Error",
                                             alt_message=f"No such job id {task_id} was found",
                                             status="failed",
                                             http_code=503)
        except redis.connection.ConnectionError:
            response_object = StatusResponse(paper=paper,
                                             message="Redis Cnx Err",
                                             alt_message="Database to read tasks status is unreachable",
                                             status="failed",
                                             http_code=503)
        # Paper exists, but task_status is unknown
        except WebError as e:
            response_object = StatusResponse(paper=paper,
                                             message=e.message,
                                             alt_message=f"Paper id: {paper_id}, task status: {paper.task_status}",
                                             status="failed",
                                             http_code=503)

    return response_object.response


@bp.route("/bht_run/<paper_id>/<file_type>", defaults={"pipeline_start_step": PipeStep.MKDIR}, methods=["GET"])
@bp.route("/bht_run/<paper_id>/<file_type>/<pipeline_start_step>", methods=["GET"])
def bht_run(paper_id, file_type, pipeline_start_step=0):
    found_file = get_paper_file(paper_id, file_type.upper())
    if found_file is None:
        flash("No file for that paper.")
        return redirect(url_for("main.papers"))

    # TODO: REFACTOR CUT START and delegate to Paper and Task models
    try:
        q = Queue(connection=redis.from_url(current_app.config["REDIS_URL"]))
        task = q.enqueue(
            get_pipe_callback(test=current_app.config["TESTING"]),
            args=(paper_id, current_app.config["WEB_UPLOAD_DIR"], file_type, pipeline_start_step),
            job_timeout=600,
        )
    except redis.connection.ConnectionError:
        response_object = StatusResponse(paper=None,
                                         status="failed",
                                         paper_id=int(paper_id),
                                         message="Failed, no Redis",
                                         alt_message="System to run tasks is unreachable",
                                         http_code=503)
        return response_object.response

    paper = db.session.get(Paper, paper_id)
    paper.set_task_id(task.get_id())
    paper.set_task_status("queued")
    paper.set_cat_path(None)
    # TODO: CUT END

    response_object = StatusResponse(paper=paper,
                                     status="success", task_status="queued", paper_id=paper.id,
                                     http_code=202)
    return response_object.response


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
    events_dict_list = HpEvent.get_events_dicts(found_events)

    # now get some stats and pack as dict
    processed_papers = Paper.query.filter_by(cat_in_db=True).all()
    all_missions = Mission.query.all()
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

    return render_template(
        "events.html", events=events_dict_list, paper=paper, db_stats=_db_stats
    )


@bp.route("/admin", methods=["GET"])
def admin():
    # build a list of papers with catalogs not already inserted in db
    page = request.args.get('page', 1, type=int)
    _query = Paper.query.filter(Paper.cat_in_db == False, Paper.cat_path != 'None')

    _paginated_papers = _query.paginate(
        page=page,
        per_page=current_app.config["PER_PAGE"],
        error_out=False
    )

    return render_template(
        "admin.html", papers=_paginated_papers
    )


@bp.route("/catalogs", methods=["GET", "POST"])
def catalogs():
    """UI page to retrieve catalogs by mission"""
    params = {
        "selected_missions": [1],
        "duration_max": 2880,  # 2 days in minutes
        "duration_min": 0,  # 1 hour in minutes
        "nconf_min": 0.980,
    }
    if request.method == "POST":
        params["selected_missions"] = [int(i) for i in request.form.getlist("missions")]
        params["duration_max"] = int(request.form.get("duration-max"))
        params["duration_min"] = int(request.form.get("duration-min"))
        params["nconf_min"] = float(request.form.get("nconf-min"))

    # look for events corresponding to selected missions
    found_events = []
    selected_missions_names = []
    for m_id in params["selected_missions"]:
        _m = Mission.query.get(m_id)
        if _m is not None:
            selected_missions_names.append(_m.name)
            found_events.extend(_m.hp_events)

    # translate to dict list, then pandas dataframe, and filter
    # then translate back to dict (pd.to_records)
    events_dict_list = HpEvent.get_events_dicts(found_events)
    if len(events_dict_list) > 0:
        _events_df = pd.DataFrame.from_records(events_dict_list)
        min_timedelta = pd.Timedelta(minutes=params["duration_min"])
        max_timedelta = pd.Timedelta(minutes=params["duration_max"])
        _events_df = _events_df[_events_df["duration"] < max_timedelta]
        _events_df = _events_df[_events_df["duration"] > min_timedelta]
        _events_df = _events_df[_events_df["nconf"] > params["nconf_min"]]

        events_dict_list = _events_df.to_records()

    # for web display, rebuild all missions as dict, with only fields we need
    _missions = [
        {"name": _m.name, "id": _m.id, "num_events": len(_m.hp_events)}
        for _m in db.session.query(Mission).order_by(Mission.name).all()
        if len(_m.hp_events) > 0
    ]

    # now get some stats and pack as dict

    _db_stats = {
        "total_events": len(found_events),
        "filtered_events": len(events_dict_list),
        "selected_missions": selected_missions_names,
    }

    return render_template(
        "catalogs.html",
        missions=_missions,
        events=events_dict_list,
        events_ids=",".join([str(_e.id) for _e in events_dict_list]),
        db_stats=_db_stats,
        params=params,
    )


@bp.route("/statistics")
def statistics():
    params = {"bins": 200,
              "nconf_min": 0.95,
              "nconf_max": 0.999}
    return render_template("statistics.html", params=params)


#  - - - - - - - - - - - - - - - - - - A P I  R O U T E S  - - - - - - - - - - - - - - - - - - - - #

@bp.route("/api/nconf_dist_graph", methods=["POST"])
def api_nconf_dist_graph():
    params = {"bins": int(request.json.get("bins")),
              "nconf_max": float(request.json.get("nconf-max")),
              "nconf_min": float(request.json.get("nconf-min"))}

    import matplotlib
    matplotlib.use('Agg')  # Prevent no gui error
    import matplotlib.pyplot as plt
    import io
    import base64

    events_dict_list = HpEvent.get_events_dicts(HpEvent.query.all())
    df = pd.DataFrame(events_dict_list)

    df = df[(df['nconf'] >= params['nconf_min']) & (df['nconf'] <= params['nconf_max'])]

    # Prevent no gui error
    plt.ioff()
    # Create plot
    plt.figure(figsize=(15, 6))
    plt.hist(df['nconf'], bins=params['bins'], facecolor='#ffca2c', color='#ffca2c', edgecolor='black', linewidth=0.5)
    plt.title('NConf Distribution Values')
    plt.xlabel('NConf')
    plt.ylabel('Frequency')

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    return jsonify({'plot_url': f'data:image/png;base64,{plot_url}'})


# @bp.route("/api/catalogs", methods=["GET"])
# def api_catalogs():
#     """Get the events list for a given mission
#     :parameter: mission_id  in get request
#     :return: list of events as dict
#     """
#     mission_id = request.args.get("mission_id")
#     mission = Mission.query.get(mission_id)
#     # TODO: REFACTOR extract to event model method and merge common code with api_catalog_txt
#     events_list = [
#         event.get_dict()
#         for event in HpEvent.query.filter_by(mission_id=mission_id).order_by(
#             HpEvent.start_date
#         )
#     ]
#     response_object = {
#         "status": "success",
#         "data": {
#             "events": events_list,
#             "mission": {
#                 "id": mission.id,
#                 "name": mission.name,
#                 "num_events": len(mission.hp_events),
#             },
#         },
#     }
#     return jsonify(response_object)


@bp.route("/api/catalogs/txt", methods=["GET"])
def api_catalogs_txt():
    """Download the txt version of the catalog for the given mission

    To do that,
     - retrieve from db all events related to that mission id
     - Dump this events list to a text file.


    :parameter: mission_id  in get request
    :return: catalog text file as attachment
    """
    events_ids = request.args.get("events_ids")
    mission_id = request.args.get("mission_id")
    if events_ids:
        today = datetime.now().strftime("%Y%M%dT%H%m%S")
        catalog_name = f"web_request_{today}"
        events_ids = events_ids.split(",")
        events_list = []
        # Optimised sqlalchemy request
        events_list = HpEvent.query.filter(HpEvent.id.in_(events_ids)).all()
        events_dict_list = HpEvent.get_events_dicts(events_list)
    elif mission_id:
        mission = db.session.get(Mission, mission_id) if mission_id else None
        catalog_name = mission.name
        if mission_id is None or mission is None:
            return Response(
                f"No valid parameters for url: {mission_id} {mission}",
                status=400,
            )
        events_dict_list = HpEvent.get_events_dicts(
            HpEvent.query.filter_by(mission_id=mission_id).order_by(HpEvent.start_date)
        )
    else:
        flash(f"Missing arguments 'mission_id' or 'events_ids[]' empty", "warning")
        return redirect(url_for("main.catalogs"))
    catalog_txt_stream = rows_to_catstring(
        events_dict_list,
        catalog_name,
        columns=[
            "start_time",
            "stop_time",
            "doi",
            "sats",
            "insts",
            "regs",
            "d",
            "r",
            "conf",
            "nconf",
        ],
    )

    date_now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bht_pipeline_version = current_app.config["BHT_PIPELINE_VERSION"]
    # TODO: build catalog name else where, may be from some bht.method()
    file_name = f"{catalog_name}_{date_now}_bibheliotech_V{bht_pipeline_version}.txt"
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
