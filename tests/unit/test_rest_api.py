#
# This projects offers somme RESTFull api
# usually through some /api/ like urls
# The current file is here for basic testing those routes.
#
# More tests on specific use cases will occur in the functional/ directory
import json

import pytest
from flask import url_for

from tests.conftest import skip_istex
from web.models import Paper


class TestPapersRoutes:
    def test_paper_del(self, client, paper_for_test, db):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/paper/del' page is requested (POST)
        THEN check that the response has deleted the paper in db
        """
        paper_id = paper_for_test.id
        response = client.get(f"/paper/del/{paper_id}")
        assert response.status_code == 302
        assert db.session.get(Paper, paper_id) is None


class TestUploadPdf:
    def test_upload_with_wrongparam(self, client):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/upload_from_url' page is posted with wrong parameter
        THEN check that a '400' status code is returned
        """
        response = client.post("/upload_from_url", data={"wrong_param": None})
        assert response.status_code == 400
        assert b"No valid parameters" in response.data

    def test_upload_pdf(self, client):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/upload_from_url' page is posted with correct parameter
        THEN check that a '302' status code is returned
        """
        response = client.post(
            "/upload_from_url",
            data={
                "file_url": "https://angeo.copernicus.org/articles/28/233/2010/angeo-28-233-2010.pdf"
            },
        )
        assert response.status_code == 302

    def test_upload_pdf_postonly(self, client):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/upload_from_url' page is get from (GET)
        THEN check that a '405' status code is returned
        """
        response = client.get("/upload_from_url")
        assert response.status_code == 405


@skip_istex
class TestIstexRoutes:
    def test_istex_from_url(self, client, istex_url):
        """
        GIVEN a Flask application and an ISTEX url
        WHEN the '/istex_from_url' form action is posted to (POST)
        THEN check that a '200' status code is returned
             with proper response content
        """
        response = client.post("/istex", data={"istex_req_url": istex_url})
        assert response.status_code == 200
        assert b"The solar wind from a stellar perspective" in response.data

    def test_istex_upload_id(self, client, istex_id, db):
        """
        GIVEN a Flask application and an ISTEX ID
        WHEN the '/istex_upload_istex_id' REST endpoint is posted to json request
        THEN check that a '201' status code is returned
             with proper response content (json with success and paper id)
        """
        import json

        response = client.post(
            "/istex_upload_id",
            data=json.dumps(dict(istex_id=istex_id)),
            content_type="application/json",
        )
        # first check we go success to request
        assert response.status_code == 201
        # then test that paper was indeed inserted in db
        paper = db.session.get(Paper, response.json["paper_id"])
        assert paper.title == "Proton-proton collisional age to order solar wind types"


class TestCatalogsRoutes:
    def test_api_push_catalog(self, client, paper_for_test):
        pushcatalog_url = url_for("main.api_push_catalog")
        response = client.post(
            pushcatalog_url,
            data=json.dumps({"paper_id": 1}),
            content_type="application/json",
        )
        assert response.status_code == 201

    @pytest.mark.skip(reason="Waiting for db refactoring")
    def test_api_catalogs_txt(self, client, hpevents_in_db):
        catalog_txt_url = url_for("main.api_catalogs_txt")
        response = client.get(catalog_txt_url, query_string={"mission_id": 1})
        assert response.status_code == 200
        assert "attachment" in response.headers["Content-Disposition"]
        assert "filename" in response.headers["Content-Disposition"]

    def test_api_catalogs_txt_wrong_param(self, client):
        response = client.get(url_for("main.api_catalogs_txt"))
        assert response.status_code == 400
        assert b"Missing arguments" in response.data

    def test_api_catalogs_txt_wrong_param_2(self, client):
        response = client.get(
            url_for("main.api_catalogs_txt"), query_string={"wrong_param": 1}
        )
        assert response.status_code == 400
        assert b"Missing arguments" in response.data
