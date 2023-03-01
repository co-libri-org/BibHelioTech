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
        base_url = request.url + url_for("main.index")
        firefox_driver.get(base_url)
        elem = firefox_driver.find_element(By.LINK_TEXT, "BibHelioTech")
        assert elem is not None
