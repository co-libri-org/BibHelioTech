import pytest
from flask import url_for, request, current_app
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from tests.functional.conftest import skip_selenium
from web.models import Paper


@skip_selenium
@pytest.mark.usefixtures("live_server")
class TestRunPapers:
    def test_papers_added(self, firefox_driver, paperslist_for_tests):
        print("------ memory", current_app.config["SQLALCHEMY_DATABASE_URI"])
        papers_url = request.url + url_for("main.papers")
        assert len(paperslist_for_tests) > 0
        papers_in_db = Paper.query.all()
        assert len(papers_in_db) == 6
        firefox_driver.get(papers_url)
        elems = firefox_driver.find_elements(By.XPATH, "//tbody/tr")
        assert len(elems) == len(paperslist_for_tests)

    def test_have_run_btn(self, firefox_driver, paperslist_for_tests):
        papers_url = request.url + url_for("main.papers")
        firefox_driver.get(papers_url)
        # select all buttons of class run-bht with title containing "TXT" string
        elems = firefox_driver.find_elements(
            By.XPATH, "//button[contains(@class,'run-bht') and contains(@title, 'TXT')]"
        )
        assert len(elems) == 6

    def test_click_run_btn(self, firefox_driver, paperslist_for_tests):
        papers_url = request.url + url_for("main.papers")
        firefox_driver.get(papers_url)
        first_run_btn = firefox_driver.find_element(By.CLASS_NAME, "run-bht")
        paper_id = first_run_btn.get_attribute("data-paper_id")
        first_run_btn.click()
        status_btn_id = f"bht-status-{paper_id}"
        status_btn = firefox_driver.find_element(By.ID, status_btn_id)
        wait = WebDriverWait(firefox_driver, 20)
        have_it = wait.until(
            ec.text_to_be_present_in_element((By.ID, status_btn_id), "started")
        )
        assert have_it
        assert "started" in status_btn.text
