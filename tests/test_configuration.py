#
# Various tests to check configuration and pytest fixtures
#
import os.path

from bht_config import yml_settings
from web.models import Paper


def test_configuration(app):
    """
    GIVEN the flask app create pattern
    WHEN an instance is created
    THEN check configuration
    """
    assert "resources-tests" in app.config["BHT_RESOURCES_DIR"]


def test_txt_for_test(txt_for_test):
    """
    GIVEN the txt fixture
    WHEN used
    THEN make sure it exists
    @param txt_for_test:
    @return:
    """
    assert os.path.isfile(txt_for_test)


def test_paper_with_cat(paper_with_cat):
    """
    GIVEN the paper_with_cat fixture
    WHEN used
    THEN check attributes
    """
    assert type(paper_with_cat) is Paper
    assert paper_with_cat.has_cat
    assert "105194angeo282332010_bibheliotech_V1.txt" in paper_with_cat.cat_path


def test_paper_for_test(paper_for_test):
    """
    GIVEN the paper_for_test fixture
    WHEN used
    THEN check attributes
    """
    assert type(paper_for_test) is Paper
    assert not paper_for_test.has_cat
    assert paper_for_test.has_pdf
    assert not paper_for_test.cat_in_db


def test_yml_configuration():
    """
    GIVEN a yml config file
    WHEN some parameter is read
    THEN check it returns awaited value
    """
    assert "DATA/Paper" in yml_settings["BHT_PAPERS_DIR"]
