from flask import Flask
from web.config import Config


def create_app(config_instance=None):
    app = Flask(__name__)

    if not config_instance:
        config_instance = Config()
    app.config.from_object(config_instance)

    from web.main import bp as main_bp
    app.register_blueprint(main_bp)

    return app
