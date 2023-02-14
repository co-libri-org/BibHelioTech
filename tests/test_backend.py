import os
import shutil
import unittest

from bht_config import yml_settings
from bht.published_date_finder import published_date_finder
from bht.GROBID_generator import GROBID_generation
from tests.conftest import skip_slow_test


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
