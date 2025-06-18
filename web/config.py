import os

from bht_config import yml_settings, BHT_ROOT_DIR


class Config(object):
    LOG_TO_STDOUT = True
    LOG_TO_FILE = True
    TESTING = False
    SECRET_KEY = (
        os.environ.get("SECRET_KEY")
        or b"\x82\xde\x96\xc5L\xb4c\xd5\x17\x12*\x12\xd3\xd4\xb7\xf5"
    )
    ALLOWED_EXTENSIONS = ["pdf", "txt"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
        yml_settings["WEB_DB_DIR"], "bht_web.db"
    )


class ProdConfig(Config):

    # flask-htpasswd extension configuration
    FLASK_HTPASSWD_PATH = os.path.join(BHT_ROOT_DIR, ".htpasswd")
    FLASK_SECRET = b"\x82\xde\x96\xc5L\xb4c\xd5\x17\x12*\x12\xd3\xd4\xb7\xf5"
    FLASK_AUTH_ALL = True


class DevConfig(Config):
    # Set DEBUG with `flask run --debug` option
    TESTING = True
    WEB_UPLOAD_DIR = os.path.join(BHT_ROOT_DIR, "dev-upload/")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
        yml_settings["WEB_DB_DIR"], "bht_web-dev.db"
    )


class TestConfig(Config):
    TESTING = True
    # Set DEBUG with `flask run --debug` option
    # Ignore @login_required decorator
    # LOGIN_DISABLED = True
    WEB_UPLOAD_DIR = os.path.join(BHT_ROOT_DIR, "test-upload/")
    # Set sqlite to in memory for tests
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
        yml_settings["WEB_DB_DIR"], "bht_web-test.db"
    )
    # SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    BHT_RESOURCES_DIR = os.path.join(BHT_ROOT_DIR, "resources-tests")
