from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from web.config import Config

db = SQLAlchemy()


def create_app(config_class=Config):
    app = Flask(__name__)

    config_instance = config_class()
    app.config.from_object(config_instance)

    db.init_app(app)

    from web.main import bp as main_bp

    app.register_blueprint(main_bp)

    return app
