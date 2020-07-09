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
import datetime
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

# Initialization
app = Flask(__name__)
labels = setup.labels
time_limit = setup.time_limit
high_score_list_size = setup.top_n
num_games = setup.num_games
certainty_threshold = setup.certainty_threshold

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
    return "Yes, we're up"


@app.route("/startGame")
def start_game():
    """
        Starts a new game by providing the client with a unique token.
    """
    # start a game and insert it into the games table
    token = uuid.uuid4().hex
    labels_list = random.choices(labels, k=num_games)
    date = datetime.datetime.today()
    models.insert_into_games(token, json.dumps(labels_list), 0.0, date)
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
    if game.session_num > num_games:
        return "Game limit reached", 400

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
        return "No image submitted", 400

    # Retrieve the image and check if it satisfies constraints
    image = request.files["image"]
    if not allowed_file(image):
        return "Image does not satisfy constraints", 415

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
        time_used < time_limit
        and best_guess == label
        and best_certainty >= certainty_threshold
    )
    # End game if player win or loose
    if has_won or time_used >= time_limit:
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

    if game.session_num == num_games + 1:
        score = game.play_time
        date = datetime.date.today()
        models.insert_into_scores(name, score, date)

    # Clean database for unnecessary data
    models.delete_session_from_game(token)
    models.delete_old_games()
    return "OK", 200


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


@app.route("/viewHighScore")
def view_high_score():
    """
        Read highscore from database. Return top n of all time and top n of last 24 hours.
    """
    #read top n overall high score
    top_n_high_scores = models.get_top_n_high_score_list(high_score_list_size)
    #read daily high score
    daily_high_scores = models.get_daily_high_score()
    data = {
        "daily": daily_high_scores,
        "total": top_n_high_scores
    }
    return json.jsonify(data), 200
