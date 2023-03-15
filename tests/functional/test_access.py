import pytest
from flask import url_for, request, current_app
from selenium.webdriver.common.by import By


@pytest.mark.usefixtures("live_server")
class TestBasicAccess:
    def test_access(self):
        assert (
            f'http://localhost:{str(current_app.config["LIVESERVER_PORT"])}/'
            == request.url
        )

    def test_index(self, firefox_driver):
        """
        GIVEN a running flask app
        WHEN home is called
        THEN check title element has text
        """
        base_url = request.url + url_for("main.index")
        firefox_driver.get(base_url)
        elem = firefox_driver.find_element(By.LINK_TEXT, "BibHelioTech")
        assert elem is not None

    def test_catalogs_page(self, firefox_driver, paper_for_test):
        """
        GIVEN a running flask app and an inserted Paper
        WHEN the catalogs/ page is called
        THEN check it has un_added catalogs
        """
        base_url = request.url + url_for("main.catalogs")
        firefox_driver.get(base_url)
        elem = firefox_driver.find_element(By.XPATH, "//h4[@class='mb-5']")
        assert elem is not None
        assert elem.text == "Available Missions:"
