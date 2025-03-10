#
# The following tests belong to the unit directory
# and thus intend to simply test the flask routes,
# and pages return.
#
# For more detailed tests on specific use cases, please take look at the functional/ tests
#
from filetype import filetype
from flask import current_app

from tests.conftest import skip_slow_test
from web.main.routes import get_file_from_url
from web.models import Paper, file_to_db


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

    # TODO: TEST  getfilefromurl with bad url
    # TODO: TEST  getfilefromurl with no file
    # TODO: TEST  getfilefromurl with wrong file  format

    def test_save_to_db(self, pdf_for_test, tmp_path_factory):
        """
        GIVEN a file object and a name (from disk file)
        WHEN the save_to_db() is called (in an app_context, see autouse fixture)
        THEN check that the Paper object is saved
        """
        import os

        upload_dir = tmp_path_factory.mktemp("upload_dir")

        with open(pdf_for_test, "rb") as _fd:
            p_id = file_to_db(_fd.read(), os.path.basename(pdf_for_test), upload_dir)
        guessed_title = os.path.basename(pdf_for_test).replace(".pdf", "")
        paper = Paper.query.filter_by(title=guessed_title).one_or_none()
        assert paper is not None
        assert paper.id == p_id
        assert paper.pdf_path == os.path.join(
            upload_dir, os.path.basename(pdf_for_test)
        )


class TestCatalogsPage:
    def test_catalog_page(self, client):
        """
        GIVEN a flask app
        WHEN the catalog page is requested
        THEN check that page is returned
        """
        response = client.get("/catalogs")
        assert response.status_code == 200
        assert b"Available Missions" in response.data


class TestAdminPage:

    def test_admin_page(self, client, paper_with_cat):
        """
        GIVEN a flask app and paper_for_test in db
        WHEN the catalog page is requested
        THEN check that page contains non_added catalogs
        """
        response = client.get("/admin")
        assert response.status_code == 200
        assert b"Catalogs to add in database:" in response.data


class TestIstexPage:

    def test_papers_uploadfield(self, client):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/papers' page is requested (GET)
        THEN check that the response is valid
        """
        response = client.get("/istex")
        assert response.status_code == 200
        assert b"from new File" in response.data

    def test_papers_pdffield(self, client):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/papers' page is requested (GET)
        THEN check that the response has download pdf field
        """
        response = client.get("/istex")
        assert response.status_code == 200
        assert b"from URL" in response.data

    def test_istex_page(self, client):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/istex' page is get from (GET)
        THEN check that a '200' status code is returned
             with proper content
        """
        response = client.get("/istex")
        assert response.status_code == 200
        assert b"Get papers from Istex api" in response.data
