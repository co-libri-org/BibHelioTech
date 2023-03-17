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
        if not _app.debug and not _app.testing:
            # send ERROR by Mail if possible
            if _app.config.get("MAIL_SERVER"):
                auth = None
                if _app.config["MAIL_USERNAME"] or _app.config["MAIL_PASSWORD"]:
                    auth = (_app.config["MAIL_USERNAME"], _app.config["MAIL_PASSWORD"])
                secure = None
                if _app.config["MAIL_USE_TLS"]:
                    secure = ()
                mail_handler = SMTPHandler(
                    mailhost=(_app.config["MAIL_SERVER"], _app.config["MAIL_PORT"]),
                    fromaddr="no-reply@" + _app.config["MAIL_SERVER"],
                    toaddrs=[_app.config["DEV_EMAIL"]],
                    subject="App Failure",
                    credentials=auth,
                    secure=secure,
                )
                mail_handler.setLevel(logging.ERROR)
                _app.logger.addHandler(mail_handler)

        if _app.config.get("LOG_TO_STDOUT") and _app.config["LOG_TO_STDOUT"]:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            stream_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
                )
            )
            _app.logger.addHandler(stream_handler)
        else:
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
