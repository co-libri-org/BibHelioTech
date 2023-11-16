import logging
import os.path

from bht.logging import init_logger


class TestLogging:

    def test_init_logger(self):
        _logger = init_logger()
        assert type(_logger) is logging.Logger

    def test_logfile_created(self, test_logfile):
        assert not os.path.isfile(test_logfile)
        _logger = init_logger(test_logfile)
        assert os.path.isfile(test_logfile)
