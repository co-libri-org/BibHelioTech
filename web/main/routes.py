import glob
import os

from werkzeug.utils import secure_filename

from . import bp
from flask import send_from_directory, render_template, current_app, request, flash, redirect, url_for


@bp.route('/')
def index():
    return render_template("index.html", name=current_app.config['BHT_DATA_DIR'])


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@bp.route('/uploads/<name>')
@bp.route('/uploads')
def uploads(name=None):
    if not name:
        # get all uploaded pdf
        pdf_list = glob.glob(os.path.join(current_app.config['WEB_UPLOAD_DIR'],'*.pdf'))
        return render_template('uploads.html', pdf_list=pdf_list)
    else:
        flash("Uploaded "+name)
        return redirect(url_for('main.uploads'))
    # return send_from_directory(current_app.config["WEB_UPLOAD_DIR"], name)


@bp.route('/upload', methods=['GET', 'POST'])
def upload_file():
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
            return redirect(url_for('main.uploads', name=filename))
    return render_template("upload_form.html")
