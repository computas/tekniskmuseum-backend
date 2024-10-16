#! /usr/bin/env python
"""
    API with endpoints runned by Flask. Contains these endpoints:
        / : Responds if the API is up
        /startGame : Provide client with unique player_id used for identification
        /getLabel : Provide client with a new word
        /classify : Classify an image
        /endGame : Signal from client that the game is finished
        /viewHighScore : Provide clien with the highscore from the game
"""
import uuid
import os
import json
from datetime import datetime
import pytz
from PIL import Image, ImageChops
from io import BytesIO
from src import storage
from . import models
import src.models as shared_models
from src.utilities import setup
from src.utilities.keys import Keys
from src.customvision.classifier import Classifier
from flask import Blueprint, current_app, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug import exceptions as excp


singleplayer = Blueprint("singleplayer", __name__)

# Initialize CV classifier
classifier = Classifier()


@singleplayer.route("/")
def hello():
    current_app.logger.info("We're up!")
    return "Yes, we're up", 200


@singleplayer.route("/startGame")
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
    labels = shared_models.get_n_labels(setup.NUM_GAMES, difficulty_id)
    today = datetime.today()
    shared_models.insert_into_games(
        game_id, json.dumps(labels), today, difficulty_id
    )
    shared_models.insert_into_players(player_id, game_id, "Playing")
    # return game data as json object
    data = {
        "player_id": player_id,
    }
    current_app.logger.info(
        "singleplayer /startGame! difficulty_id: "
        + str(difficulty_id)
        + " player_id: "
        + str(player_id)
        + " game_id: "
        + str(game_id)
        + " date: "
        + str(today)
        + " labels: "
        + str(labels)
    )
    return json.dumps(data), 200


@singleplayer.route("/getLabel", methods=["POST"])
def get_label():
    """
    Provides the client with a new word.
    """
    player_id = request.values["player_id"]
    lang = request.values["lang"]
    player = shared_models.get_player(player_id)
    game = shared_models.get_game(player.game_id)

    # Check if game complete
    if game.session_num > setup.NUM_GAMES:
        raise excp.BadRequest("Number of games exceeded")

    labels = json.loads(game.labels)
    label = labels[game.session_num - 1]
    current_app.logger.info(
        "singleplayer /getLabel "
        + " player_id: "
        + str(player_id)
        + " label: "
        + str(label)
    )
    if lang == "NO":
        norwegian_label = shared_models.to_norwegian(label)
        data = {"label": norwegian_label}
        return json.dumps(data), 200
    else:
        data = {"label": label}
        return json.dumps(data), 200


@singleplayer.route("/classify", methods=["POST"])
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
    player = shared_models.get_player(player_id)
    clientRound = request.values.get("client_round_num", None)
    game = shared_models.get_game(player.game_id)
    server_round = game.session_num
    if clientRound is not None and int(clientRound) < game.session_num:
        raise excp.BadRequest(
            "Server-round number larger than request/client. Probably a request processed out of order"
        )
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
        shared_models.update_game_for_player(
            player.game_id, player_id, 1, "Done"
        )
        # save image
        try:
            storage.save_image(image, label, best_certainty)
        except Exception as e:
            current_app.logger.error(e)
        # Update game state to be done
        game_state = "Done"
        # Insert statistic for label
        models.insert_into_label_success(
            label=label, is_success=has_won, date=datetime.now()
        )
    # translate labels into norwegian
    if lang == "NO":
        translation = shared_models.get_translation_dict()
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
    current_app.logger.info(
        "singleplayer /classify " + " player_id: " + str(player_id)
    )
    return json.dumps(data), 200


@singleplayer.route("/postScore", methods=["POST"])
def post_score():
    """
    Endpoint for ending game consisting of NUM_GAMES sessions.
    """
    data = request.get_json()
    player_id = data.get("player_id")
    score = float(data.get("score"))
    difficulty_id = int(data.get("difficulty_id"))

    player = shared_models.get_player(player_id)
    game = shared_models.get_game(player.game_id)

    if game.session_num != setup.NUM_GAMES + 1:
        raise excp.BadRequest("Game not finished")

    today = datetime.today()
    shared_models.insert_into_scores(player_id, score, today, difficulty_id)

    current_app.logger.info(
        "singleplayer /classify " + " player_id: " + str(player_id)
    )
    return json.dumps({"success": "OK"}), 200


@singleplayer.route("/viewHighScore")
def view_high_score():
    """
    Read highscore from database. Return top n of all time and daily high
    scores.
    """
    difficulty_id = request.values["difficulty_id"]
    # read top n overall high score
    top_n_high_scores = shared_models.get_top_n_high_score_list(
        setup.TOP_N, difficulty_id=difficulty_id
    )
    # read daily high score
    daily_high_scores = shared_models.get_daily_high_score(
        difficulty_id=difficulty_id
    )
    data = {
        "daily": daily_high_scores,
        "total": top_n_high_scores,
    }
    current_app.logger.info(
        "singleplayer /viewHighScore "
        + " difficulty_id: "
        + str(difficulty_id)
    )
    return json.dumps(data), 200


@singleplayer.route("/getExampleDrawings", methods=["POST"])
def get_n_drawings_by_label():
    """
    Returns n images from the blob storage container with the given label.
    """
    data = request.get_json()
    number_of_images = data["number_of_images"]
    label = data["label"]
    lang = data["lang"]
    if lang == "NO":
        label = shared_models.to_english(label)

    image_urls = shared_models.get_n_random_example_images(
        label, number_of_images
    )
    try:
        images = storage.get_images_from_relative_url(image_urls)
    except Exception as e:
        current_app.logger.error(e)
    current_app.logger.info(
        "singleplayer /getExampleDrawings " + " label: " + str(label)
    )
    return json.dumps(images), 200


@singleplayer.errorhandler(Exception)
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
        current_app.logger.error(error)
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
    shared_models.insert_into_user(username, hashed_psw)
    response = {"response": "user added"}
    return json.dumps(response), 200


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
        shared_models.update_game_for_player(game_id, player_id, 1, "Done")
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
