import glob
import os

from werkzeug.utils import secure_filename

from flask import send_from_directory, render_template, current_app, request, flash, redirect, url_for, send_file

from . import bp
from web.errors import *
from bht.__main__ import run_file as bht_run_file


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@bp.route('/')
def index():
    return render_template("index.html")

@bp.route('/about')
def about():
    return render_template("index.html", message='To fill in')

@bp.route('/configuration')
def configuration():
    return render_template("configuration.html", configuration=current_app.config)


@bp.route('/papers/<name>')
@bp.route('/papers')
def papers(name=None):
    if not name:
        # get all uploaded pdf
        pdf_list = glob.glob(os.path.join(current_app.config['WEB_UPLOAD_DIR'], '*.pdf'))
        papers_list = [os.path.basename(pdf_file).replace(".pdf", "") for pdf_file in pdf_list]
        return render_template('papers.html', papers_list=papers_list)
    else:
        flash("Uploaded " + name)
        return redirect(url_for('main.papers'))


@bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_dir = current_app.config['WEB_UPLOAD_DIR']
            if not os.path.isdir(upload_dir):
                os.makedirs(upload_dir)
            file.save(os.path.join(upload_dir, filename))
            return redirect(url_for('main.papers', name=filename))
    return render_template("upload_form.html")


@bp.route('/pdf2catalog/<pdf_file>')
def pdf2catalog(pdf_file):
    # finde pdf file from ... upload dir
    found_pdf_file = os.path.join(current_app.config['WEB_UPLOAD_DIR'], pdf_file)
    if not os.path.isfile(found_pdf_file):
        flash(f"No such file {found_pdf_file}")
        return redirect(url_for("main.index"))
    catalog_path = bht_run_file(found_pdf_file, current_app.config['WEB_UPLOAD_DIR'])
    # catalog_file = os.path.basename(catalog_path)
    if not os.path.isfile(catalog_path):
        raise WebResultError(f"Unable to build catalog file for {pdf_file}")
    paper_id = os.path.basename(pdf_file).replace(".pdf", "")
    return redirect(url_for('main.catalog', catalog_dir=paper_id))


@bp.route('/catalog/<catalog_dir>', methods=['GET'])
def catalog(catalog_dir):
    search_pattern = os.path.join(current_app.config['WEB_UPLOAD_DIR'], '**', catalog_dir, '*bibheliotech' '*.txt')
    print(search_pattern)
    catalog_paths = glob.glob(search_pattern, recursive=True)
    if len(catalog_paths) == 0:
        raise WebResultError(f"Not any catalog for paper in {catalog_dir}")
    found_file = catalog_paths[0]
    print(f' -+ -+ -+ -+ -+ -+ -+ -+ -+ -+ > > {found_file}')
    if not os.path.isfile(found_file):
        flash(f"No such file {catalog_dir}")
        raise WebResultError(f"No such file {found_file}")
        return redirect(url_for('main.index'))
    return send_file(found_file)


@bp.route('/catalogs', methods=['GET'])
def catalogs():
    _catalogs = glob.glob(os.path.join(current_app.config['BHT_PAPERS_DIR'], '**', '*bibhelio*.txt'), recursive=True)
    return render_template("catalogs.html", catalogs=_catalogs)
