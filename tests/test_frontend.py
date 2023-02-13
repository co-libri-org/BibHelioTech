def test_papers_with_uploadfield(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/papers' page is requested (GET)
    THEN check that the response is valid
    """
    response = test_client.get("/papers")
    assert response.status_code == 200
    assert b"Upload new File" in response.data
