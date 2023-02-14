import os

from bht_config import yml_settings


class Config(object):
    SECRET_KEY = (
        os.environ.get("SECRET_KEY")
        or b"\x82\xde\x96\xc5L\xb4c\xd5\x17\x12*\x12\xd3\xd4\xb7\xf5"
    )
    ALLOWED_EXTENSIONS = ["pdf"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
        yml_settings["WEB_DB_DIR"], "bht_web.db"
    )

    def __init__(self):
        # Get config keys from the settings dictionnary
        self.__dict__.update(yml_settings)


class TestConfig(Config):
    TESTING = True
    DEBUG = True
    # ignores @login_required decorator
    # LOGIN_DISABLED = True
    UPLOAD_FOLDER = "test-upload/"
    # Should be set to in memory for tests
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
