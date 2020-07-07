#! /usr/bin/env python
"""
    API with endpoints runned by Flask. Contains three key endpoints:
        - hello(): return a dummy string
        - start_game(): starts a game
        - submit_answer(): takes an image, returns the prediction and time used by user
"""
import uuid
import random
import time
import sys
import os
import logging
from webapp import storage
from webapp import models
from webapp import setup
from customvision.classifier import Classifier
from io import BytesIO
from PIL import Image
from flask import Flask
from flask import request
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy

# Global variables
app = Flask(__name__)
app.config.from_object("webapp.config.Config")
models.db.init_app(app)
models.create_tables(app)
classifier = Classifier()
labels = setup.labels
time_limit = setup.time_limit

if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)


@app.route("/")
def hello():
    app.logger.info("We're up!")
    return "Yes, we're up"


@app.route("/startGame")
def start_game():
    """
        Starts a new game. A unique token is generated to keep track of game.
        A random label is chosen for the player to draw. Startime is
        recorded to calculate elapsed time when the game ends. Name can be
        either None or a name and is not unique. Will be sent from frontend.   
    """
    # start a game and insert it into the games table
    start_time = time.time()
    token = uuid.uuid4().hex
    label = random.choice(labels)
    models.insert_into_games(token, start_time, label)

    # return game data as json object
    data = {
        "token": token,
        "label": label,
        "start_time": start_time,
    }
    return jsonify(data), 200


@app.route("/submitAnswer", methods=["POST"])
def submit_answer():
    """
        Endpoint for user to submit drawing. Drawing is classified with Custom
        Vision.The player wins if the classification is correct and the time
        used is less than the time limit.
    """
    stop_time = time.time()

    # Check if image submitted correctly
    if "image" not in request.files:
        return "No image submitted", 400
    image = request.files["image"]
    if not allowed_file(image):
        return "Image does not satisfy constraints", 415

    # get classification from customvision
    best_guess, certainty = classifier.predict_image(image)

    # use token submitted by player to find game
    token = request.values["token"]
    start_time, label = models.query_game(token)

    # check if player won the game
    time_used = stop_time - start_time
    has_won = time_used < time_limit and best_guess == label

    # save image in blob storage
    storage.save_image(image, label)

    # save score in highscore table
    name = request.values["name"]
    score = time_used
    models.insert_into_scores(name, score)

    # return json response
    data = {
        "certainty": certainty,
        "guess": best_guess,
        "correctLabel": label,
        "hasWon": has_won,
        "timeUsed": time_used,
    }
    return jsonify(data), 200


def allowed_file(image):
    """
        Check if image satisfies the constraints of Custom Vision.
    """
    if image.filename == "":
        return False

    # Check if the filename is of PNG type
    png = image.filename.endswith(".png") or image.filename.endswith(".PNG")
    # Ensure the file isn't too large
    too_large = len(image.read()) > 4000000
    # Ensure the file has correct resolution
    image.seek(0)
    height, width = Image.open(BytesIO(image.stream.read())).size
    image.seek(0)
    correct_res = (height >= 256) and (width >= 256)
    if not png or too_large or not correct_res:
        return False
    else:
        return True
