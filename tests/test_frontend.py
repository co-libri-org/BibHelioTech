import os.path

from tests import conftest
from web.main.routes import get_file_from_url


@conftest.skip_slow_test
class TestFrontUtils:
    def test_get_file_from_url(self):
        file_path = get_file_from_url(
            "https://angeo.copernicus.org/articles/28/233/2010/angeo-28-233-2010.pdf"
        )
        assert os.path.isfile(file_path)


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
                "pdf_url": "https://api.istex.fr/ark:/67375/80W-QC194JKZ-X/fulltext.pdf"
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
