import json

from flask import url_for


class TestApiCatalogs:
    def test_api_push_catalog(self, test_client):
        pushcatalog_url = url_for("main.api_push_catalog")
        response = test_client.post(
            pushcatalog_url,
            data=json.dumps({"paper_id": 1}),
            content_type="application/json",
        )
        assert response.status_code == 201
