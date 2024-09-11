from flask import Flask
from src.multiplayer import multiplayer
from src.webapp import singleplayer
from src.utilities import setup
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from utilities.keys import Keys
import logging
from logging.handlers import RotatingFileHandler
import uuid
import os
import re
import json
from datetime import datetime, timezone, timedelta
from PIL import Image
from PIL import ImageChops
from threading import Thread
from io import BytesIO
from webapp import storage
from webapp import models
from flask import request
from flask import session
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from werkzeug import exceptions as excp
from flask import Blueprint
from flask_migrate import Migrate


def create_app():
    app = Flask(__name__)
    app.register_blueprint(multiplayer, url_prefix='/multiplayer')
    app.register_blueprint(singleplayer, url_prefix='/')

    if Keys.exists("CORS_ALLOWED_ORIGIN"):
        CORS(app, resources={r"/*": {"origins": Keys.get("CORS_ALLOWED_ORIGIN"), "supports_credentials": True}})
    else:
        CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": True}})

    app.config.from_object("utilities.setup.Flask_config")

    #Config logging
    logging.basicConfig(filename='record.log', level=logging.INFO, filemode="w", format="%(asctime)s %(levelname)s %(message)s")

    #max file size 4 MB
    handler = RotatingFileHandler(
        filename='record.log',
        maxBytes=4 * 1024 * 1024,
        backupCount=5
    )

    app.logger.addHandler(handler)

    if __name__ != "__main__":
        gunicorn_logger = logging.getLogger("gunicorn.error")
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

    try:
        # Set up DB and models
        models.db.init_app(app)
        models.create_tables(app)
        models.populate_difficulty(app)
        # Point to correct CSV file
        webapp_dir = os.path.dirname(os.path.abspath(__file__))
        csv_file_path = os.path.join(webapp_dir, "dict_eng_to_nor_difficulties_v2.csv")
        models.seed_labels(app, csv_file_path)
        app.logger.info("Backend was able to communicate with DB. ")
        models.populate_example_images(app)
    except Exception:
        #error is raised by handle_exception()
        print("Error when contacting DB in Azure")
    
    migrate = Migrate(app, models.db)

    return app
