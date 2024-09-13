#!/usr/bin/env python
"""
    This file contains all entry points for the API. The API will use
    Websockets for most of the communication, although an HTTP route to
    root has been established, since it makes it easy to check if the
    application is live.
"""
from flask_socketio import emit, send, join_room
from flask import request
from flask import Blueprint
from PIL import Image
from PIL import ImageChops
from io import BytesIO
from datetime import datetime
import json
import uuid
import time
import random
from utilities.difficulties import DifficultyId
from utilities.languages import Language
from . import models
import src.models as shared_models
from src import storage
from utilities.exceptions import UserError
from utilities import setup
from customvision.classifier import Classifier
from flask import current_app as app
from src.extensions import socketio


multiplayer = Blueprint('multiplayer', __name__)
classifier = Classifier()


@socketio.on("connect")
def connect():
    app.logger.info("===== client " + request.sid + " connected =====")


@socketio.on("disconnect")
def disconnect():
    """
        When a player disconnects from a session this function tells the
        other player in the room that someone left and deletes all records in the
        database connected to the session.
    """
    player_id = request.sid
    player = shared_models.get_player(player_id)
    game = shared_models.get_game(player.game_id)
    data = {"player_disconnected": True}
    models.update_game_for_player(game.game_id, player_id, 0, "Disconnected")
    opponent = models.get_opponent(game.game_id, player_id)
    if opponent is None or opponent.state == "Disconnected":
        emit("playerDisconnected", json.dumps(data), room=player_id)
        shared_models.delete_session_from_game(game.game_id)
    else:
        emit("playerDisconnected", json.dumps(data), room=game.game_id)
    app.logger.info("=== client " + request.sid + " disconnected ===")


@socketio.on("message")
def handle_message(message):
    app.logger.info("client: " + str(message))


@socketio.on("filetest")
def handle_filetest(json_data, image):
    app.logger.info(json_data)
    with open("harambe.png", "wb") as f:
        f.write(image)


@socketio.on("joinGame")
def handle_joinGame(json_data):
    """
        Check if mulitplayer table exists for the optional pair_id.
        * If check is false create new mulitplayer game.
        * If check is true insert player where player2 is none and start
          the game.
    """
    data = json.loads(json_data or 'null')
    try:
        difficulty_id = data["difficulty_id"]
        pair_id = data["pair_id"]
    except (KeyError, TypeError):
        pair_id = ''
        app.logger.error("No pair id for " + request.sid)
    app.logger.info("pair id: " + pair_id + " player id: " + request.sid)
    player_id = request.sid
    #  Players join their own room as well
    join_room(player_id)
    game_id = models.check_player_2_in_mulitplayer(player_id, pair_id)

    if game_id is not None:
        # Update mulitplayer table by inserting player_id for player_2 and
        # change state of palyer_1 in PIG to "Ready"
        models.update_mulitplayer(player_id, game_id)
        shared_models.insert_into_players(player_id, game_id, "Ready")
        player_nr = "player_2"
        is_ready = True

    else:
        game_id = uuid.uuid4().hex
        labels = models.get_n_labels(setup.NUM_GAMES, difficulty_id)
        today = datetime.today()
        shared_models.insert_into_games(
            game_id, json.dumps(labels), today, difficulty_id)

        shared_models.insert_into_players(player_id, game_id, "Waiting")
        models.insert_into_mulitplayer(game_id, player_id, pair_id)
        player_nr = "player_1"
        is_ready = False

    data = {"player_nr": player_nr, "player_id": player_id, "game_id": game_id}
    state_data = {"ready": is_ready}
    join_room(game_id)
    # Emit message with player-state to each player triggering the event
    emit("joinGame", data, sid=player_id)
    # Emit message with game-state to both players each time a player
    # triggers the event
    emit("joinGame", state_data, room=game_id)


@socketio.on("getLabel")
def handle_getLabel(json_data):
    """
        Event for providing both players with a new label.
    """
    player_id = request.sid
    data = json.loads(json_data)
    game_id = data["game_id"]

    opponent = models.get_opponent(game_id, player_id)
    models.update_game_for_player(game_id, player_id, 0, "Ready")
    models.update_game_for_player(game_id, opponent.player_id, 0, "Ready")

    label = get_label(game_id)
    app.logger.info("returned label: " + json.dumps(label))
    emit("getLabel", json.dumps(label), room=game_id)


@socketio.on("postScore")
def handle_postScore(json_data):
    data = json.loads(json_data)
    app.logger.info(data)
    player_id = data.get("player_id")
    score = float(data.get("score"))
    difficulty_id = int(data.get("difficulty_id"))
    assert isinstance(difficulty_id, int)

    today = datetime.today()
    shared_models.insert_into_scores(player_id, score, today, difficulty_id)


@socketio.on("viewHighScore")
def view_high_score(json_data):
    """
        Read highscore from database. Return top n of all time and daily high
        scores.
    """
    difficulty_id = DifficultyId.Multiplayer
    data = json.loads(json_data)
    game_id = data["game_id"]
    # read top n overall high score
    top_n_high_scores = models.get_top_n_high_score_list(
        setup.TOP_N, difficulty_id=difficulty_id)
    # read daily high score
    daily_high_scores = models.get_daily_high_score(
        difficulty_id=difficulty_id)
    data = {
        "daily": daily_high_scores,
        "total": top_n_high_scores,
    }

    emit("viewHighScore", json.dumps(data), room=game_id)


@socketio.on("getExampleDrawings")
def get_example_drawings(json_data, emitEndpoint="getExampleDrawings"):
    """
        Get example drawings from the database
    """
    data = json.loads(json_data)
    game_id = data["game_id"]
    number_of_images = data["number_of_images"]

    label = data["label"]
    lang = data["lang"]
    if (lang == "NO"):
        label = shared_models.to_english(label)

    example_drawing_urls = shared_models.get_n_random_example_images(
        label, number_of_images)
    example_drawings = storage.get_images_from_relative_url(
        example_drawing_urls)
    emit(emitEndpoint, json.dumps(example_drawings), room=game_id)


@socketio.on("getExampleDrawingsP1")
def get_example_drawings_player_1(json_data):
    get_example_drawings(json_data, emitEndpoint="getExampleDrawingsP1")


@socketio.on("getExampleDrawingsP2")
def get_example_drawings_player_2(json_data):
    get_example_drawings(json_data, emitEndpoint="getExampleDrawingsP2")


@socketio.on("classify")
def handle_classify(data, image, correct_label=None):
    """
        WS event for accepting images for classification
        params: data: {"game_id": str: the game_id you get from joinGame,
                       "time_left": float: the time left until the game is over}
               image: binary string with the image data
    """
    image_stream = BytesIO(image)

    allowed_file(image_stream)

    player_id = request.sid
    game_id = data["game_id"]
    time_left = data["time_left"]
    lang: Language = data["lang"]

    if correct_label is None:
        game = shared_models.get_game(game_id)
        labels = json.loads(game.labels)
        correct_label = labels[game.session_num - 1]

    # Check if the image hasn't been drawn on
    bytes_img = Image.open(image_stream).convert('RGB')
    if white_image(bytes_img):
        response = white_image_data(
            correct_label, time_left, game_id, player_id
        )
        if response["gameState"] != "Done":
            emit("prediction", response)
            return

    image_stream.seek(0)
    certainty, best_guess = classifier.predict_image_by_post(image_stream)
    best_certainty = certainty[best_guess]

    time_out = (time_left <= 0)

    if time_out:
        # to break race condition if both players timeout
        time.sleep(0.5 * random.random())
        storage.save_image(image, correct_label, best_certainty)
        player = shared_models.get_player(player_id)
        opponent = models.get_opponent(game_id, player_id)
        if opponent.state == "Done":
            if player.state != "Done":
                # update state for player and increase session_id
                models.update_game_for_player(game_id, player_id, 1, "Done")
            emit("roundOver", {"round_over": True}, room=game_id)
        else:
            # update state for player
            models.update_game_for_player(game_id, player_id, 0, "Done")
        return

    has_won = (correct_label == best_guess) and (time_left > 0)

    if lang == Language.Norwegian:

        response = {
            "certainty": translate_probabilities(certainty),
            "guess": shared_models.to_norwegian(best_guess),
            "correctLabel": shared_models.to_norwegian(correct_label),
            "hasWon": has_won,
        }

    else:
        response = {
            "certainty": certainty,
            "guess": best_guess,
            "correctLabel": correct_label,
            "hasWon": has_won,
        }

    emit("prediction", response)

    if has_won:
        storage.save_image(image, correct_label, best_certainty)
        player = shared_models.get_player(player_id)
        opponent = models.get_opponent(game_id, player_id)
        if opponent.state == "Done":
            if player.state != "Done":
                # update state for player and increase session_id
                models.update_game_for_player(game_id, player_id, 1, "Done")
            emit("roundOver", {"round_over": True}, room=game_id)
        else:
            # update state for player
            models.update_game_for_player(game_id, player_id, 0, "Done")


@socketio.on("endGame")
def handle_endGame(json_data):
    """
        Event which ends the final game of the two players. The players provide
        their scores and the player with the highest score is deemed the winner.
        The two scores are finally stored in the database.
    """
    data = json.loads(json_data)
    # Get data from given player
    game_id = data["game_id"]
    score_player = data["score"]
    player_id = data["player_id"]
    if shared_models.get_game(game_id).session_num != setup.NUM_GAMES + 1:
        pass
        # raise excp.BadRequest("Game not finished")
    # Insert score information into db
    # Create a list containing player data which is sent out to both players
    return_data = {"score": score_player, "playerId": player_id}
    # Retrieve the opponent (client) to pass on the score to
    opponent = models.get_opponent(game_id, player_id)
    emit("endGame", json.dumps(return_data), room=opponent.player_id)
    shared_models.delete_old_games()


@socketio.on_error()
def error_handler(error):
    """
        Captures all Exceptions raised. If error is an Exception, the
        error message is returned to the client. Else the error is
        logged.
    """
    app.logger.error(error)

    if isinstance(error, UserError):
        emit("error", str(error))


def get_label(game_id) -> dict[str, str]:
    """
        Provides the client with a new word in both languages.
    """
    game = shared_models.get_game(game_id)

    # Check if game complete
    if game.session_num > setup.NUM_GAMES:
        send("Number of games exceeded")

    labels = json.loads(game.labels)
    label: str = labels[game.session_num - 1]
    norwegian_label = models.to_norwegian(label)
    data = {"label": label, "norwegian_label": norwegian_label}
    return data


def translate_probabilities(labels):
    """
        translate the labels in a probability dictionary to norwegian
    """
    translation_dict = shared_models.get_translation_dict()
    return dict(
        [(translation_dict[label], prob) for label, prob in labels.items()]
    )


def allowed_file(image):
    """
        Check if image satisfies the constraints of Custom Vision.
    """
    # Ensure the file isn't too large
    too_large = len(image.read()) > setup.MAX_IMAGE_SIZE
    # Ensure the file has correct resolution
    image.seek(0)
    pimg = Image.open(image)
    height, width = pimg.size
    correct_res = (height >= setup.MIN_RESOLUTION) and (
        width >= setup.MIN_RESOLUTION
    )

    if str(type(pimg)) == "JpegImageFile":
        is_png = pimg.format == "PNG"
    else:
        is_png = pimg

    image.seek(0)

    if not is_png or too_large or not correct_res:
        raise UserError("Wrong image format")


def white_image(image):
    """
        Check if the image provided is completely white.
    """
    if ImageChops.invert(image).getbbox() is None:
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
        game_state = "Done"

    data = {
        "certainty": 1.0,
        "guess": setup.WHITE_IMAGE_GUESS,
        "correctLabel": label,
        "hasWon": False,
        "gameState": game_state,
    }
    return data
