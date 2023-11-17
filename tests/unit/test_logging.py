import logging
import os.path

from bht.logging import init_logger


class TestLogging:

    def test_init_logger(self):
        _logger = init_logger()
        assert type(_logger) is logging.Logger

    def test_init_logger_clear(self):
        _logger = init_logger()
        _logger = init_logger(clear=True)
        assert len(_logger.handlers) == 2

    def test_logger_fixture(self, logger):
        assert type(logger) is logging.Logger

    def test_logfile_created(self, test_logfile):
        assert not os.path.isfile(test_logfile)
        _logger = init_logger(test_logfile)
        _logger.debug("Test debug message")
        _logger.info("Test info message")
        assert os.path.isfile(test_logfile)
