from azure.monitor.opentelemetry import configure_azure_monitor
from src.utilities.keys import Keys
import os
# Only configure Azure Monitor when not running FLASK migrations or running locally
if not os.getenv("FLASK_RUN_FROM_CLI") and os.getenv("IS_PRODUCTION"):
    configure_azure_monitor(connection_string=Keys.get("INSIGHTS_CONNECTION_STRING"))
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
from . import models
from src.extensions import db, socketio
from flask import Flask
from flask_migrate import Migrate
from datetime import timedelta
from src.multiplayer import multiplayer
from src.singleplayer import singleplayer


def create_app():

  
    app = Flask(__name__)
    app.register_blueprint(multiplayer, url_prefix="/")
    app.register_blueprint(singleplayer, url_prefix="/")

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
        engineio_logger=False,
    )

    app.config.from_object("src.utilities.setup.Flask_config")

    # Config logging
    logging.basicConfig(
        filename="record.log",
        level=logging.INFO,
        filemode="w",
        format="%(asctime)s %(levelname)s %(message)s",
    )
    # max file size 1 MB
    handler = RotatingFileHandler(
        filename="record.log", maxBytes=1024 * 1024, backupCount=5
    )
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

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
        models.populate_example_images(app)
        app.logger.info("Backend was able to create DB in Azure. ")
    except Exception as e:
        app.logger.error("Error when creating DB in Azure. " + str(e))

    try:
        Migrate(app, db)
    except Exception as e:
        app.logger.error("Error when migrating DB " + str(e))

    app.logger.info("Backend is running. ")
    return app, socketio
