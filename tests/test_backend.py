import os
import shutil
import unittest

from bht_config import yml_settings
from bht.published_date_finder import published_date_finder
from bht.GROBID_generator import GROBID_generation
from tests.conftest import skip_slow_test
from web import db
from web.models import Paper


class TestDb:
    def test_db_created(self):
        """
        GIVEN a Flask app (see autouse fixture in conftest.py )
        WHEN db session is used for saving an object
        THEN check that the object was saved
        """
        my_path = "/paper/path/to.pdf"
        my_title = "Paper Title"
        paper = Paper(title=my_title, pdf_path=my_path)
        db.session.add(paper)
        db.session.commit()
        found_paper = Paper.query.filter_by(title=my_title).one()
        assert found_paper.pdf_path == my_path


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.pdf_directory = yml_settings["BHT_PAPERS_DIR"]
        test_pdf_file_orig = os.path.join(
            yml_settings["BHT_RESSOURCES_DIR"], "2016GL069787-test.pdf"
        )
        self.test_pdf_file_dest = os.path.join(
            self.pdf_directory, "2016GL069787-test.pdf"
        )
        shutil.copy(test_pdf_file_orig, self.test_pdf_file_dest)
        self.test_tei_file = os.path.join(self.pdf_directory, "2016GL069787.tei.xml")

    def tearDown(self):
        for file in [self.test_pdf_file_dest, self.test_tei_file]:
            if os.path.isfile(file):
                os.remove(file)


class AdsTestCase(BaseTestCase):
    def test_published_date(self):
        from sys import version

        token = "IXMbiJNANWTlkMSb4ea7Y5qJIGCFqki6IJPZjc1m"  # API Key
        doi = "10.1002/2016gl069787"
        found_date = published_date_finder(token, version, doi)
        self.assertEqual("2017-04-01T00:00:00Z", found_date)


@skip_slow_test
class GrobidTestCase(BaseTestCase):
    def test_grobid_generation(self):
        GROBID_generation(self.pdf_directory)  # generate the XML GROBID file
        self.assertTrue(os.path.isfile(self.test_tei_file))
