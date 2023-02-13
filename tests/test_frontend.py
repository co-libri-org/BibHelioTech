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
