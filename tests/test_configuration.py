def test_configuration(app):
    assert "resources-tests" in app.config["BHT_RESOURCES_DIR"]
