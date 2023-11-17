from logging.handlers import RotatingFileHandler

import logging
from bht_config import yml_settings


def init_logger(logfile=yml_settings["BHT_LOGFILE_PATH"], clear=False):
    logger = logging.getLogger('bht_logger')

    # remove all handlers if any
    if clear and len(logger.handlers):
        for h in list(logger.handlers):
            logger.removeHandler(h)

    # singleton pattern, don't init twice
    if len(logger.handlers):
        return logger

    # setting the lowest level allows to later restrict other loggers
    logger.setLevel(logging.DEBUG)

    # file handler
    file_formatter = logging.Formatter('%(asctime)s :: [%(levelname)s] :: %(message)s')
    file_handler = RotatingFileHandler(logfile, 'a', 1000000, 7)
    file_loglevel = logging.getLevelName(yml_settings["BHT_LOGLEVEL_LOGFILE"])
    file_handler.setLevel(file_loglevel)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # console handler
    console_formatter = logging.Formatter('[%(levelname)s] %(message)s')
    console_handler = logging.StreamHandler()
    console_loglevel = logging.getLevelName(yml_settings["BHT_LOGLEVEL_CONSOLE"])
    console_handler.setLevel(console_loglevel)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    logger.info(f"NEW LOGGER : {logfile}")
    return logger
