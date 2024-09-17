from flask import Flask
from src.multiplayer import multiplayer
from src.singleplayer import singleplayer
from flask_cors import CORS
from src.utilities.keys import Keys
import logging
from logging.handlers import RotatingFileHandler
import os
from . import models
from src.extensions import db, socketio


def create_app():
    app = Flask(__name__)
    app.register_blueprint(multiplayer, url_prefix="/")
    app.register_blueprint(singleplayer, url_prefix="/")

    if Keys.exists("CORS_ALLOWED_ORIGIN"):
        CORS(
            app,
            resources={
                r"/*": {
                    "origins": Keys.get("CORS_ALLOWED_ORIGIN"),
                    "supports_credentials": True,
                }
            },
        )
        socketio.init_app(
            app,
            cors_allowed_origins=Keys.get("CORS_ALLOWED_ORIGIN"),
            logger=True,
        )
    else:
        socketio.init_app(app, cors_allowed_origins="*", logger=True)
        CORS(
            app,
            resources={r"/*": {"origins": "*", "supports_credentials": True}},
        )

    app.config.from_object("src.utilities.setup.Flask_config")

    # Config logging
    logging.basicConfig(
        filename="src/record.log",
        level=logging.INFO,
        filemode="w",
        format="%(asctime)s %(levelname)s %(message)s",
    )

    # max file size 1 MB
    handler = RotatingFileHandler(
        filename="record.log", maxBytes=1024 * 1024, backupCount=5
    )

    app.logger.addHandler(handler)

    if __name__ != "__main__":
        gunicorn_logger = logging.getLogger("gunicorn.error")
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

    try:
        # Set up DB and models
        db.init_app(app)
        models.create_tables(app)
        models.populate_difficulty(app)
        # Point to correct CSV file
        src_dir = os.path.dirname(os.path.abspath(__file__))
        csv_file_path = os.path.join(
            src_dir, "dict_eng_to_nor_difficulties_v2.csv"
        )
        models.seed_labels(app, csv_file_path)
        app.logger.info("Backend was able to communicate with DB. ")
        models.populate_example_images(app)
    except Exception:
        # error is raised by handle_exception()
        app.logger.error("Error when contacting DB in Azure")

    return app, socketio
