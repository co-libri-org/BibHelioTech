import json

from flask import url_for


class TestApiCatalogs:
    def test_api_push_catalog(self, test_client, paper_for_test):
        pushcatalog_url = url_for("main.api_push_catalog")
        response = test_client.post(
            pushcatalog_url,
            data=json.dumps({"paper_id": 1}),
            content_type="application/json",
        )
        assert response.status_code == 201

    def test_api_catalogs_txt(self, test_client, hpevents_in_db):
        catalog_txt_url = url_for("main.api_catalogs_txt")
        response = test_client.get(catalog_txt_url, query_string={"mission_id": 1})
        assert response.status_code == 200
        assert "attachment" in response.headers["Content-Disposition"]
        assert "filename" in response.headers["Content-Disposition"]

    def test_api_catalogs_txt_wrong_param(self, test_client):
        response = test_client.get(url_for("main.api_catalogs_txt"))
        assert response.status_code == 400
        assert b"No valid parameters" in response.data

    def test_api_catalogs_txt_wrong_param_2(self, test_client):
        response = test_client.get(
            url_for("main.api_catalogs_txt"), query_string={"wrong_param": 1}
        )
        assert response.status_code == 400
        assert b"No valid parameters" in response.data
