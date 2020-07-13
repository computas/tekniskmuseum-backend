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
from wtforms import form
from wtforms import fields
from wtforms import validators
import flask_admin
import flask_login
from werkzeug.security import generate_password_hash, check_password_hash

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
    labels_list = random.sample(labels, num_games)
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
    time_left = float(request.values["time"])
    # Get label for game session
    game = models.get_record_from_game(token)
    labels = json.loads(game.labels)
    label = labels[game.session_num - 1]

    best_certainty = certainty[best_guess]
    # The player has won if the game is completed within the time limit
    has_won = (
        time_left > 0
        and best_guess == label
        and best_certainty >= certainty_threshold
    )
    
    if has_won:
        # save image in blob storage
        storage.save_image(image, label)
        # Update game state to be done
        game_state = "Done"
    
    elif time_left <= 0:
        game_state = "Done"
    
    if game_state == "Done":
        # Get cumulative time
        cum_score = game.score + time_left
        # Increment session_num
        session_num = game.session_num + 1
        # Add to games table
        models.update_game(token, session_num, cum_score)

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
        score = game.score
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

# ADMIN STUFF:
@app.route("/auth", methods=["POST"])
def authenticate():
    """
        Endpoint for administrating the application; clear/drop tables,
        retrain ML, clear training set.
    """
    email = request.values["email"]
    password = request.values["password"]

    user = models.get_user(email)

    if user is None:
        raise HTTPException("Invalid username or password", 401)  # Some custom exception here

    if not check_password_hash(user.password, password)
        raise Exception("Invalid password")  # Some custom exception here

    return "OK", 200


@app.route("/adminPage/<action>", methods=["POST"])
def admin_page():
    if action == "dropTable":
        @login_required
        def drop_table():
            table = request.values["table"]
            # If table is None all tables is dropped - should this be prevented??
            models.drop_table(table)

    elif action == "trainML":
        @login_required
        def train_ml():
            pass

    elif action == "clearTrainSet":
        @login_required
        def clear_train_set():
            pass



def add_user(username, email, password):
    """
        Add user to user table in db.
    """
    # Do we want a cond check_secure_password(password)?
    hashed_psw = generate_password_hash(password, method="pbkdf2:sha256", salt_length=8)
    models.insert_into_user(username, email, password)