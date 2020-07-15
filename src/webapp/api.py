#! /usr/bin/env python
"""
    API with endpoints runned by Flask. Contains three endpoints:
        / : Responds if the API is up
        /startGame : Provide client with unique token used for identification
        /getLabel : Provide client with a new word
        /classify : Classify an image
        /endGame : Signal from client that the game is finished
        /viewHighScore : Provide clien with the highscore from the game
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
from utilities.setup import NUM_GAMES, CERTAINTY_THRESHOLD, TOP_N
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
    game_id = uuid.uuid4().hex
    token = uuid.uuid4().hex
    labels = models.get_n_labels(NUM_GAMES)
    today = datetime.datetime.today()
    models.insert_into_games(game_id, json.dumps(labels), today)
    models.insert_into_player_in_game(token, game_id, 0.0)
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
    player = models.get_record_from_player_in_game(token)
    game = models.get_record_from_game(player.game_id)

    # Check if game complete
    if game.session_num > NUM_GAMES:
        raise excp.BadRequest("Number of games exceeded")

    labels = json.loads(game.labels)
    label = labels[game.session_num - 1]
    data = {
        "label": label
    }
    return json.jsonify(data), 200


@app.route("/classify", methods=["POST"])
def classify():
    """
        Classify endpoint for continious guesses.
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
    time_left = float(request.values["time"])
    # Get label for game session
    player = models.get_record_from_player_in_game(token)
    game = models.get_record_from_game(player.game_id)
    labels = json.loads(game.labels)
    label = labels[game.session_num - 1]
    best_certainty = certainty[best_guess]
    # The player has won if the game is completed within the time limit
    has_won = (
        time_left > 0
        and best_guess == label
        and best_certainty >= CERTAINTY_THRESHOLD
    )
    # End game if player win or loose
    if has_won or time_left <= 0:
        # save image in blob storage
        storage.save_image(image, label)
        # Get cumulative time
        cum_time = player.play_time + time_left
        # Increment session_num
        session_num = game.session_num + 1
        # Add to games table
        models.update_game_for_player(
            player.game_id, token, session_num, cum_time
        )
        # Update game state to be done
        game_state = "Done"

    # translate
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
    score = request.values["score"]
    player = models.get_record_from_player_in_game(token)
    game = models.get_record_from_game(player.game_id)

    if game.session_num != NUM_GAMES + 1:
        return excp.BadRequest("Game not finished")

    today = datetime.date.today()
    models.insert_into_scores(name, score, today)

    # Clean database for unnecessary data
    models.delete_session_from_game(player.game_id)
    models.delete_old_games()
    return "OK", 200


@app.route("/viewHighScore")
def view_high_score():
    """
        Read highscore from database. Return top n of all time and all of
        last 24 hours.
    """
    # read top n overall high score
    top_n_high_scores = models.get_top_n_high_score_list(TOP_N)
    # read daily high score
    daily_high_scores = models.get_daily_high_score()
    data = {
        "daily": daily_high_scores,
        "total": top_n_high_scores,
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
    is_png = image.content_type == "image/png"
    # Ensure the file isn't too large
    too_large = len(image.read()) > 4000000
    # Ensure the file has correct resolution
    image.seek(0)
    height, width = Image.open(BytesIO(image.stream.read())).size
    image.seek(0)
    correct_res = (height >= 256) and (width >= 256)
    if not is_png or too_large or not correct_res:
        raise excp.UnsupportedMediaType("Wrong image format")
