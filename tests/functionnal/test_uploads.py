import pytest
from flask import url_for, request
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from tests.functionnal.conftest import skip_selenium


@skip_selenium
@pytest.mark.usefixtures("live_server")
class TestUploadPdf:
    def test_upload_new_file(self, pdf_for_test, firefox_driver):
        """
        GIVEN a Flask app (see autouse fixture in conftest.py )
        WHEN pdf file is uploaded through form
        THEN check we find corresponding paper in db
        """
        # get papers page
        papers_url = request.url + url_for("main.papers")
        firefox_driver.get(papers_url)
        # set file to upload in input field
        input_elmt = firefox_driver.find_element(By.XPATH, "//input[@name='file']")
        input_elmt.send_keys(pdf_for_test)
        # send to backend
        firefox_driver.find_element(By.XPATH, "//form").submit()
        # check result page
        wait = WebDriverWait(firefox_driver, 2)
        have_it = wait.until(
            ec.presence_of_element_located((By.XPATH, "//ul[@class='flashes']"))
        )
        assert have_it
        # flash_elmt = firefox_driver.find_element(By.XPATH, "//ul[@class='flashes']/li")
        # assert flash_elmt.text == 'ho'
        # look for paper in db
