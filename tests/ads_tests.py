import unittest
from bht.published_date_finder import published_date_finder


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass


class AdsTestCase(BaseTestCase):

    def test_published_date(self):
        from sys import version
        token = 'IXMbiJNANWTlkMSb4ea7Y5qJIGCFqki6IJPZjc1m'  # API Key
        doi = '10.1002/2016gl069787'
        found_date = published_date_finder(token, version, doi)
        self.assertEqual('2017-04-01T00:00:00Z', found_date)
