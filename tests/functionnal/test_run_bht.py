import pytest
from flask import url_for, request
from selenium.webdriver.common.by import By


@pytest.mark.usefixtures("live_server")
def test_papers_added(firefox_driver, paperslist_for_tests):
    papers_url = request.url + url_for("main.papers")
    firefox_driver.get(papers_url)
    elems = firefox_driver.find_elements(By.XPATH, "//tbody/tr")
    assert len(paperslist_for_tests) > 0
    assert len(elems) == len(paperslist_for_tests)


@pytest.mark.usefixtures("live_server")
def test_have_run_btn(firefox_driver, paperslist_for_tests):
    papers_url = request.url + url_for("main.papers")
    firefox_driver.get(papers_url)
    elems = firefox_driver.find_elements(By.CLASS_NAME, "run-bht")
    assert len(elems) == 6
