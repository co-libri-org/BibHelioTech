from pprint import pprint

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from web.config import Config

db = SQLAlchemy()


def create_app(config_instance=None):
    app = Flask(__name__)

    if not config_instance:
        config_instance = Config()
    app.config.from_object(config_instance)

    db.init_app(app)

    from web.main import bp as main_bp
    app.register_blueprint(main_bp)

    return app
