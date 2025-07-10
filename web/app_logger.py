import logging
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
            stream_loglevel = logging.getLevelName(_app.config.get("BHT_LOGLEVEL_CONSOLE"))
            stream_handler.setLevel(stream_loglevel)
            stream_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
                )
            )
            _app.logger.addHandler(stream_handler)

        if _app.config.get("LOG_TO_FILE") and _app.config["LOG_TO_FILE"]:
            log_filename = _app.config.get("BHT_LOGFILE_PATH")
            file_handler = RotatingFileHandler(
                log_filename, maxBytes=10240, backupCount=10
            )
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
                )
            )
            file_loglevel = logging.getLevelName(_app.config.get("BHT_LOGLEVEL_LOGFILE"))
            file_handler.setLevel(file_loglevel)
            _app.logger.addHandler(file_handler)
