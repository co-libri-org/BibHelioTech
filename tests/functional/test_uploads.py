import os

import pytest
from flask import url_for, request
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from tests.conftest import skip_selenium


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
        has_flash_msg = wait.until(
            ec.presence_of_element_located((By.XPATH, "//ul[@class='flashes']"))
        )
        assert has_flash_msg

        flash_elmt = firefox_driver.find_element(By.XPATH, "//ul[@class='flashes']/li")
        assert flash_elmt.text == f"Uploaded {os.path.basename(pdf_for_test)}"

        file_table_line = firefox_driver.find_element(By.XPATH, "//tbody/tr")
        assert file_table_line
