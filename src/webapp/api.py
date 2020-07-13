#! /usr/bin/env python
"""
    API with endpoints runned by Flask. Contains three endpoints:
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
from datetime import date
from datetime import datetime
from webapp import storage
from webapp import models
from utilities import setup
from customvision.classifier import Classifier
from io import BytesIO
from PIL import Image
from flask import Flask
from flask import request
from flask import json
from flask_sqlalchemy import SQLAlchemy
from werkzeug import exceptions as excp

# Initialization and global variables
app = Flask(__name__)
LABELS = setup.labels
TIME_LIMIT = setup.time_limit
NUM_GAMES = setup.num_games
CERTAINTY_TRESHOLD = setup.certainty_threshold
HIGH_SCORE_LIST_SIZE = setup.top_n

app.config.from_object("utilities.setup.Flask_config")
models.db.init_app(app)
models.create_tables(app)
classifier = Classifier()

if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)


@app.route("/")
def hello():
    app.logger.info("We're up!")
    return "Yes, we're up", 200


@app.route("/startGame")
def start_game():
    """
        Starts a new game by providing the client with a unique token.
    """
    # start a game and insert it into the games table
    token = uuid.uuid4().hex
    labels = random.sample(LABELS, k=NUM_GAMES)
    today = str(date.today())
    models.insert_into_games(token, json.dumps(labels), 0.0, today)
    # return game data as json object
    data = {
        "token": token,
    }
    return json.jsonify(data), 200


@app.route("/getLabel", methods=["POST"])
def get_label():
    """
        Provides the client with a new word.
    """
    token = request.values["token"]
    game = models.get_record_from_game(token)

    # Check if game complete
    if game.session_num > NUM_GAMES:
        raise excp.BadRequest("Number of games exceeded")

    labels = json.loads(game.labels)
    label = labels[game.session_num - 1]
    data = {"label": label}
    return json.jsonify(data), 200


@app.route("/classify", methods=["POST"])
def classify():
    """
        Classify endpoit for continious guesses.
    """
    game_state = "Playing"
    # Check if image submitted correctly
    if "image" not in request.files:
        raise excp.BadRequest("No image submitted")

    # Retrieve the image and check if it satisfies constraints
    image = request.files["image"]
    allowed_file(image)

    best_guess, certainty = classifier.predict_image(image)
    # use token submitted by player to find game
    token = request.values["token"]
    # Get time from POST request
    time_used = float(request.values["time"])
    # Get label for game session
    game = models.get_record_from_game(token)
    labels = json.loads(game.labels)
    label = labels[game.session_num - 1]
    best_certainty = certainty[best_guess]
    # The player has won if the game is completed within the time limit
    has_won = (
        time_used < TIME_LIMIT
        and best_guess == label
        and best_certainty >= CERTAINTY_TRESHOLD)

    # End game if player win or loose
    if has_won or time_used >= TIME_LIMIT:
        # save image in blob storage
        storage.save_image(image, label)
        # Get cumulative time
        cum_time = game.play_time + time_used
        # Increment session_num
        session_num = game.session_num + 1
        # Add to games table
        models.update_game(token, session_num, cum_time)
        # Update game state to be done
        game_state = "Done"

    data = {
        "certainty": certainty,
        "guess": best_guess,
        "correctLabel": label,
        "hasWon": has_won,
        "gameState": game_state,
    }

    return json.jsonify(data), 200


@app.route("/endGame", methods=["POST"])
def end_game():
    """
        Endpoint for ending game consisting of a few sessions.
    """
    token = request.values["token"]
    name = request.values["name"]
    game = models.get_record_from_game(token)

    if game.session_num == NUM_GAMES + 1:
        score = game.play_time
        today = str(date.today())
        models.insert_into_scores(name, score, today)

    # Clean database for unnecessary data
    models.delete_session_from_game(token)
    models.delete_old_games()
    return "OK", 200


@app.route("/viewHighScore")
def view_high_score():
    """
        Read highscore from database. Return top n of all time and top n of last 24 hours.
    """
    #read top n overall high score
    top_n_high_scores = models.get_top_n_high_score_list(HIGH_SCORE_LIST_SIZE)
    #read daily high score
    daily_high_scores = models.get_daily_high_score()
    data = {
        "daily": daily_high_scores,
        "total": top_n_high_scores
    }
    return json.jsonify(data), 200


@app.errorhandler(Exception)
def handle_exception(error):
    """
       Captures all exceptions raised. If the Exception is a HTTPException the
       error message and code is returned to the client. Else the error is
       logged.
    """
    if isinstance(error, excp.HTTPException):
        # check if 4xx error. This should be returned to user.
        if error.code >= 400 and error.code < 500:
            return error
    else:
        app.logger.error(error)
        return "Internal server error", 500


def allowed_file(image):
    """
        Check if image satisfies the constraints of Custom Vision.
    """
    if image.filename == "":
        raise excp.BadRequest("No image submitted")

    # Check that the file is a png
    is_png = image.content_type == 'image/png'
    # Ensure the file isn't too large
    too_large = len(image.read()) > 4000000
    # Ensure the file has correct resolution
    image.seek(0)
    height, width = Image.open(BytesIO(image.stream.read())).size
    image.seek(0)
    correct_res = (height >= 256) and (width >= 256)
    if not is_png or too_large or not correct_res:
        raise excp.UnsupportedMediaType("Wrong image format")
