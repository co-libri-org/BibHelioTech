import os.path

from filetype import filetype
from flask import current_app

from tests.conftest import skip_slow_test, skip_istex
from web import db
from web.main.routes import get_file_from_url, pdf_to_db
from web.models import Paper


class TestCatalogs:
    def test_catalog_page(self, test_client):
        """
        GIVEN a flask app
        WHEN the catalog page is requested
        THEN check that page is returned
        """
        response = test_client.get("/catalogs")
        assert response.status_code == 200
        assert b"Catalogs by Mission" in response.data

    def test_catalog_page_2(self, test_client, paper_for_test):
        """
        GIVEN a flask app and paper_for_test in db
        WHEN the catalog page is requested
        THEN check that page contains non_added catalogs
        """
        response = test_client.get("/catalogs")
        assert response.status_code == 200
        assert b"Catalogs to add in database:" in response.data


class TestFrontUtils:
    @skip_slow_test
    def test_get_file_from_url(self):
        """
        GIVEN an url returning a pdf file
        WHEN the get_file_from_url() is called
        THEN check that the file was saved
        """
        content, file_path = get_file_from_url(
            "https://angeo.copernicus.org/articles/28/233/2010/angeo-28-233-2010.pdf"
        )
        assert filetype.guess(content).mime == "application/pdf"

    # TODO: test  getfilefromurl with bad url
    # TODO: test  getfilefromurl with no file
    # TODO: test  getfilefromurl with wrong file  format

    def test_save_to_db(self, pdf_for_test):
        """
        GIVEN a file object and a name (from disk file)
        WHEN the save_to_db() is called (in an app_context, see autouse fixture)
        THEN check that the Paper object is saved
        """
        with open(pdf_for_test, "rb") as _fd:
            p_id = pdf_to_db(_fd.read(), os.path.basename(pdf_for_test))
        guessed_title = os.path.basename(pdf_for_test).replace(".pdf", "")
        paper = Paper.query.filter_by(title=guessed_title).one_or_none()
        assert paper is not None
        assert paper.id == p_id
        assert paper.pdf_path == os.path.join(
            current_app.config["WEB_UPLOAD_DIR"], os.path.basename(pdf_for_test)
        )


class TestPapersPage:
    def test_papers_uploadfield(self, test_client):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/papers' page is requested (GET)
        THEN check that the response is valid
        """
        response = test_client.get("/papers")
        assert response.status_code == 200
        assert b"Upload new File" in response.data

    def test_papers_pdffield(self, test_client):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/papers' page is requested (GET)
        THEN check that the response has download pdf field
        """
        response = test_client.get("/papers")
        assert response.status_code == 200
        assert b"Upload from URL" in response.data


class TestPapersRoutes:
    def test_paper_del(self, test_client, paper_for_test):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/paper/del' page is requested (POST)
        THEN check that the response has deleted the paper in db
        """
        paper_id = paper_for_test.id
        response = test_client.get(f"/paper/del/{paper_id}")
        assert response.status_code == 302
        assert db.session.get(Paper, paper_id) is None


class TestUploadPdf:
    def test_upload_with_wrongparam(self, test_client):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/upload_from_url' page is posted with wrong parameter
        THEN check that a '400' status code is returned
        """
        response = test_client.post("/upload_from_url", data={"wrong_param": None})
        assert response.status_code == 400
        assert b"No valid parameters" in response.data

    def test_upload_pdf(self, test_client):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/upload_from_url' page is posted with correct parameter
        THEN check that a '302' status code is returned
        """
        response = test_client.post(
            "/upload_from_url",
            data={
                "pdf_url": "https://angeo.copernicus.org/articles/28/233/2010/angeo-28-233-2010.pdf"
            },
        )
        assert response.status_code == 302

    def test_upload_pdf_postonly(self, test_client):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/upload_from_url' page is get from (GET)
        THEN check that a '405' status code is returned
        """
        response = test_client.get("/upload_from_url")
        assert response.status_code == 405


@skip_istex
class TestIstexRoutes:
    def test_istex_page(self, test_client):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/istex' page is get from (GET)
        THEN check that a '200' status code is returned
             with proper content
        """
        response = test_client.get("/istex")
        assert response.status_code == 200
        assert b'<input type=submit value="Get ISTEX">' in response.data

    def test_istex_from_url(self, test_client, istex_url):
        """
        GIVEN a Flask application and an ISTEX url
        WHEN the '/istex_from_url' form action is posted to (POST)
        THEN check that a '200' status code is returned
             with proper response content
        """
        response = test_client.post("/istex", data={"istex_req_url": istex_url})
        assert response.status_code == 200
        assert b"The solar wind from a stellar perspective" in response.data

    def test_istex_upload_id(self, test_client, istex_id):
        """
        GIVEN a Flask application and an ISTEX ID
        WHEN the '/istex_upload_istex_id' REST endpoint is posted to json request
        THEN check that a '201' status code is returned
             with proper response content (json with success and paper id)
        """
        import json

        response = test_client.post(
            "/istex_upload_id",
            data=json.dumps(dict(istex_id=istex_id)),
            content_type="application/json",
        )
        # first check we go success to request
        assert response.status_code == 201
        # then test that paper was indeed inserted in db
        paper = db.session.get(Paper, response.json["paper_id"])
        assert paper.title == "BA3BC0C1E5A6B64AD5CBDE9C29AC2611455EE9A1"
