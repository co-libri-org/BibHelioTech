from tests.conftest import skip_istex
from web import db
from web.models import Paper


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
