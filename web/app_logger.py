import logging
import os
from logging.handlers import SMTPHandler, RotatingFileHandler

from flask.logging import default_handler


# A wrapper class that initiate the app logging
# It behaves like a flask extension
# Just call its init_app() method inside your create_app() factory
#
#   app = Flask()
#   app_logger  = AppLogger()
#   app_logger.init_app(app)


class AppLogger:
    def __init__(self, _app=None):
        if _app is not None:
            self.init_app(_app)

    def init_app(self, _app):
        _app.logger.removeHandler(default_handler)

        if _app.config.get("LOG_TO_STDOUT") and _app.config["LOG_TO_STDOUT"]:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            stream_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
                )
            )
            _app.logger.addHandler(stream_handler)

        if _app.config.get("LOG_TO_FILE") and _app.config["LOG_TO_FILE"]:
            # log INFO to file
            if not os.path.exists("logs"):
                os.mkdir("logs")
            log_filename = _app.config.get("LOG_FILENAME")
            if not log_filename:
                log_filename = "logfile.log"
            file_handler = RotatingFileHandler(
                os.path.join("logs", log_filename), maxBytes=10240, backupCount=10
            )
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
                )
            )
            file_handler.setLevel(logging.INFO)
            _app.logger.addHandler(file_handler)
