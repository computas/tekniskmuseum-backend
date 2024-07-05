#! /usr/bin/env python
"""
    API with endpoints runned by Flask. Contains three endpoints:
        / : Responds if the API is up
        /startGame : Provide client with unique player_id used for identification
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
import json
from datetime import datetime, timezone, timedelta
from PIL import Image
from PIL import ImageChops
from threading import Thread
from io import BytesIO
from webapp import storage
from webapp import models
from utilities import setup
from customvision.classifier import Classifier
from flask import Flask
from flask import request
from flask import session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from werkzeug import exceptions as excp
from utilities.keys import Keys

# Initialization app
app = Flask(__name__)
if Keys.exists("CORS_ALLOWED_ORIGIN"):
    cors = CORS(app,
                resources={r"/*": {"origins": Keys.get("CORS_ALLOWED_ORIGIN"),
                                   "supports_credentials": True}})
else:
    cors = CORS(app, resources={
                r"/*": {"origins": "*", "supports_credentials": True}})
app.config.from_object("utilities.setup.Flask_config")

# Set up DB and models
models.db.init_app(app)
models.create_tables(app)
models.populate_difficulty(app)
# Point to correct CSV file
models.seed_labels(app, "./dict_eng_to_nor_difficulties.csv")

# Initialize CV classifier
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
        Starts a new game by providing the client with a unique game id and player id.
    """
    # start a game and insert it into the games table
    difficulty_id = request.args.get("difficulty_id", default=None, type=int)
    if difficulty_id is None:
        return json.dumps({"error": "No difficulty_id provided"}), 400
    game_id = uuid.uuid4().hex
    player_id = uuid.uuid4().hex
    labels = models.get_n_labels(setup.NUM_GAMES, difficulty_id)
    today = datetime.today()
    models.insert_into_games(game_id, json.dumps(labels), today, difficulty_id)
    models.insert_into_players(player_id, game_id, "Playing")
    # return game data as json object
    data = {
        "player_id": player_id,
    }
    return json.dumps(data), 200


@app.route("/getLabel", methods=["POST"])
def get_label():
    """
        Provides the client with a new word.
    """
    player_id = request.values["player_id"]
    lang = request.values["lang"]
    player = models.get_player(player_id)
    game = models.get_game(player.game_id)

    # Check if game complete
    if game.session_num > setup.NUM_GAMES:
        raise excp.BadRequest("Number of games exceeded")

    labels = json.loads(game.labels)
    label = labels[game.session_num - 1]
    if lang == "NO":
        norwegian_label = models.to_norwegian(label)
        data = {"label": norwegian_label}
        return json.dumps(data), 200
    else:
        data = {"label": label}
        return json.dumps(data), 200


@app.route("/classify", methods=["POST"])
def classify():
    """
        Classify endpoint for continuous guesses.
    """
    game_state = "Playing"
    # Check if image submitted correctly
    if "image" not in request.files:
        raise excp.BadRequest("No image submitted")

    # Retrieve the image and check if it satisfies constraints
    lang = request.values["lang"]
    image = request.files["image"]
    allowed_file(image)
    # use player_id submitted by player to find game
    player_id = request.values["player_id"]
    # Get time from POST request
    time_left = float(request.values["time"])
    # Get label for game session
    player = models.get_player(player_id)

    clientRound = request.values.get("client_round_num", None)
    game = models.get_game(player.game_id)
    server_round = game.session_num
    if clientRound is not None and int(clientRound) < game.session_num:
        raise excp.BadRequest(
            "Server-round number larger than request/client. Probably a request processed out of order")
    labels = json.loads(game.labels)
    label = labels[game.session_num - 1]

    certainty, best_guess = classifier.predict_image_by_post(image)
    best_certainty = certainty[best_guess]
    # The player has won if the game is completed within the time limit
    has_won = (
        time_left > 0
        and best_guess == label
        and best_certainty >= setup.CERTAINTY_THRESHOLD
    )
    # End game if player win or loose
    if has_won or time_left <= 0:
        # Update session_num in game and state for player
        models.update_game_for_player(player.game_id, player_id, 1, "Done")
        # save image
        storage.save_image(image, label, best_certainty)
        # Update game state to be done
        game_state = "Done"
    # translate labels into norwegian
    if lang == "NO":
        translation = models.get_translation_dict()
        certainty_translated = dict(
            [
                (translation[label], probability)
                for label, probability in certainty.items()
            ]
        )
        data = {
            "certainty": certainty_translated,
            "guess": translation[best_guess],
            "correctLabel": translation[label],
            "hasWon": has_won,
            "gameState": game_state,
            "serverRound": server_round,
        }
    else:
        data = {
            "certainty": certainty,
            "guess": best_guess,
            "correctLabel": label,
            "hasWon": has_won,
            "gameState": game_state,
            "serverRound": server_round,
        }

    return json.dumps(data), 200


@app.route("/postScore", methods=["POST"])
def post_score():
    """
        Endpoint for ending game consisting of NUM_GAMES sessions.
    """
    data = request.get_json()
    player_id = data.get("player_id")
    score = float(data.get("score"))

    player = models.get_player(player_id)
    game = models.get_game(player.game_id)

    if game.session_num != setup.NUM_GAMES + 1:
        raise excp.BadRequest("Game not finished")

    today = datetime.today()
    models.insert_into_scores(player_id, score, today)

    # ! Need to decide if this is needed
    # Clean database for unnecessary data
    # models.delete_session_from_game(player.game_id)
    # models.delete_old_games()
    return json.dumps({"success": "OK"}), 200


@app.route("/viewHighScore")
def view_high_score():
    """
        Read highscore from database. Return top n of all time and daily high
        scores.
    """
    # read top n overall high score
    top_n_high_scores = models.get_top_n_high_score_list(setup.TOP_N)
    # read daily high score
    daily_high_scores = models.get_daily_high_score()
    data = {
        "daily": daily_high_scores,
        "total": top_n_high_scores,
    }
    return json.dumps(data), 200


@app.route("/getExampleDrawings", methods=["POST"])
def get_n_drawings_by_label():
    """
        Returns n images from the blob storage container with the given label.
    """
    n = request.args.get("n", default=None, type=int)
    label = request.values["label"]

    images = storage.get_n_random_images_from_label(n, label)
    return json.dumps(images), 200


@app.route("/auth", methods=["POST"])
def authenticate():
    """
        Endpoint for admin authentication. Returns encrypted cookie with login
        time and username.
    """
    username = request.values["username"]
    password = request.values["password"]

    user = models.get_user(username)

    if user is None or not check_password_hash(user.password, password):
        raise excp.Unauthorized("Invalid username or password")

    session["last_login"] = datetime.now(timezone.utc)
    session["username"] = username

    return json.dumps({"success": "OK"}), 200


@app.route("/admin/<action>", methods=["POST"])
def admin_page(action):
    """
        Endpoint for admin actions. Requires authentication from /auth within
        SESSION_EXPIRATION_TIME
    """
    # Check if user has valid cookie
    is_authenticated()

    if action == "clearHighScore":
        models.clear_highscores()
        return json.dumps({"success": "High scores cleared"}), 200

    elif action == "trainML":
        # Run training asynchronously
        Thread(target=classifier.retrain).start()
        return json.dumps({"success": "Training started"}), 200

    elif action == "hardReset":
        # Delete all images in CV, upload all orignal images and retrain
        classifier.delete_all_images()
        storage.clear_dataset()
        Thread(target=classifier.hard_reset_retrain).start()
        response = {"success": "All images deleted, nodel now training"}
        return json.dumps(response), 200

    elif action == "status":
        new_blob_image_count = storage.image_count()
        iteration = classifier.get_iteration()
        data = {
            "CV_iteration_name": iteration.name,
            "CV_time_created": str(iteration.created),
            "BLOB_image_count": new_blob_image_count,
        }
        return json.dumps(data), 200

    elif action == "logout":
        session.clear()
        return json.dumps({"success": "Session cleared"}), 200

    elif action == "ping":
        return json.dumps({"success": "pong"}), 200

    else:
        return json.dumps({"error": "Admin action unspecified"}), 400


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
        return json.dumps({"error": "Internal server error"}), 500


def allowed_file(image):
    """
        Check if image satisfies the constraints of Custom Vision.
    """
    if image.filename == "":
        raise excp.BadRequest("No image submitted")

    # Check that the file is a png
    is_png = image.content_type == "image/png"
    # Ensure the file isn't too large
    too_large = len(image.read()) > setup.MAX_IMAGE_SIZE
    # Ensure the file has correct resolution
    height, width = get_image_resolution(image)
    MIN_RES = setup.MIN_RESOLUTION
    correct_res = (height >= MIN_RES) and (width >= MIN_RES)
    if not is_png or too_large or not correct_res:
        raise excp.UnsupportedMediaType("Wrong image format")
    image.seek(0)


def add_user():
    """
        Add user to user table in db.
    """
    username = request.values["username"]
    password = request.values["password"]
    # Do we want a cond check_secure_password(password)?
    hashed_psw = generate_password_hash(
        password, method="pbkdf2:sha256:200000", salt_length=128
    )
    models.insert_into_user(username, hashed_psw)
    response = {"response": "user added"}
    return json.dumps(response), 200


def is_authenticated():
    """
        Check if user has an unexpired cookie. Renew time if not expired.
        Raises exception if cookie is invalid.
    """
    if "last_login" not in session:
        raise excp.Unauthorized()

    session_length = datetime.now(timezone.utc) - session["last_login"]
    is_auth = session_length < timedelta(
        minutes=setup.SESSION_EXPIRATION_TIME
    )

    if not is_auth:
        raise excp.Unauthorized("Session expired")
    else:
        session["last_login"] = datetime.now(timezone.utc)

        return True


def white_image(image):
    """
        Check if the image provided is completely white.
    """
    if not ImageChops.invert(image).getbbox():
        return True
    else:
        return False


def white_image_data(label, time_left, game_id, player_id):
    """
        Generate the json data to be returned to the client when a completely
        white image has been submitted for classification.
    """
    if time_left > 0:
        game_state = "Playing"
    else:
        models.update_game_for_player(game_id, player_id, 1, "Done")
        game_state = "Done"

    data = {
        "certainty": 1.0,
        "guess": setup.WHITE_IMAGE_GUESS,
        "correctLabel": label,
        "hasWon": False,
        "gameState": game_state,
    }
    return json.dumps(data), 200


def get_image_resolution(image):
    """
        Retrieve the resolution of the image provided.
    """
    image.seek(0)
    height, width = Image.open(BytesIO(image.stream.read())).size
    image.seek(0)
    return height, width
