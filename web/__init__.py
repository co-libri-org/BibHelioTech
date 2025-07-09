from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from bht_config import yml_settings
from web.app_logger import AppLogger
from web.config import Config, ProdConfig, DevConfig, TestConfig

import redis
from rq import Queue

redis_conn = None
task_queue = None

db = SQLAlchemy()
mig = Migrate()
app_logger = AppLogger()


def create_app(bht_env=None):
    """App factory method
    takes environment variable as arg to choose between configuration:
    production, development, testing or default

    @return: running app
    """
    app = Flask(__name__)

    # FLASK_ENV is deprecated
    # Set BHT_ENV  to choose your configuration
    # defaults to "production"
    import os

    if bht_env is None:
        bht_env = os.environ.get("BHT_ENV", "production")

    # Choose running mode, and corresponding configuration
    if bht_env == "production":
        config_instance = ProdConfig()
    elif bht_env == "development":
        config_instance = DevConfig()
    elif bht_env == "testing":
        config_instance = TestConfig()
    else:
        config_instance = Config()

    app.config.from_mapping(yml_settings)
    app.config.from_object(config_instance)

    # Make sure dirs are created
    if not os.path.isdir(app.config["WEB_UPLOAD_DIR"]):
        os.mkdir(app.config["WEB_UPLOAD_DIR"])
    if not os.path.isdir(app.config["ZIP_UPLOAD_DIR"]):
        os.mkdir(app.config["ZIP_UPLOAD_DIR"])

    # Set htpasswd protection if needed
    if "FLASK_HTPASSWD_PATH" in app.config:
        app.logger.debug(
            f"flask-htpasswd protect by: {app.config['FLASK_HTPASSWD_PATH']}"
        )
        from flask_htpasswd import HtPasswdAuth

        HtPasswdAuth(app)

    # Initialize Redis
    redis_conn = redis.from_url(app.config["REDIS_URL"])
    task_queue = Queue(connection=redis_conn)
    app.redis_conn = redis_conn
    app.task_queue = task_queue

    # Initialize other plugins
    app_logger.init_app(app)
    db.init_app(app)
    mig.init_app(app, db)

    # Initialize blueprints
    from web.main import bp as main_bp

    app.register_blueprint(main_bp)

    app.logger.debug(f"Running mode: {bht_env}")
    app.logger.debug(f"Db set to {app.config['SQLALCHEMY_DATABASE_URI']} ")
    app.logger.info(
        "#+-#+-#+-#+-#+-#+-#+-#+-#+-#+- CREATE APP -+#-+#-+#-+#-+#-+#-+#-+#-+#-+#"
    )

    return app
