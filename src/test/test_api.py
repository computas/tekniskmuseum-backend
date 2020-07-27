import os
import io
import sys
import pytest
import werkzeug
import tempfile
import datetime
from flask import json
from pytest import raises
from webapp import api
from webapp import models
from test import test_db
from test import config as cfg
from utilities import setup
from werkzeug import exceptions as excp
import PIL


@pytest.fixture
def client():
    """
        Pytest fixture which configures application for testing.
    """
    api.app.config["TESTING"] = True
    with api.app.test_client() as client:
        yield client


def test_root_example(client):
    """
        Use GET request on root and check if the response is correct.
    """
    res = client.get("/")
    assert res.data == b"Yes, we're up"


def test_start_game_wrong_request(client):
    """
        Ensure that the API returns error due to unsupported request type
        (something else than GET).
    """
    # send request to test client with empty dictionary
    res = client.post("/startGame", data=dict())
    assert(b"405 Method Not Allowed" in res.data)


def test_start_game_correct(client):
    """
        Ensure that the API doesn't return error when sumitting a GET request.
    """
    res = client.get("/startGame", data=dict())
    # Ensure that the returned dictionary contains a player_id
    assert(b"player_id" in res.data)


def test_classify_wrong_request(client):
    """
        Ensure that the API returns error due to unsupported request type
        (something else than POST).
    """
    # Submit GET request
    res = client.get("/classify")
    # Should give error since POST is required
    assert(b"405 Method Not Allowed" in res.data)


def test_classify_no_image(client):
    """
        Ensure that the API returns error when there is no image submitted
        in the request.
    """
    # Since the API checks if the image is there before anything else,
    # we don't need to include anything with the request
    res = client.post("/classify", data=dict())
    # Check if the correct error code is returned
    assert b"No image submitted" in res.data


def test_classify_wrong_image(client):
    """
        Ensure that the API returns error when the image submitted in the
        request doesn't comply with the constraints checked for in the
        allowedFile function.
    """
    # Start time, player_id and user doesn't need to be valid, since the error is
    # supposed to be caught before these are used
    time = 0
    player_id, user = "", ""
    # Submit answer with the given parameters and get results
    res = classify_helper(
        client, cfg.API_PATH_DATA, cfg.API_IMAGE1, time, player_id, user
    )
    assert b"415 Unsupported Media Type" in res.data


def test_classify_white_image_data(client):
    """
        Ensure that the API returns the correct json data when an image
        consisting of only white pixels is submitted.
    """
    time = 0
    user = ""
    # Need to start a new game to get a token we can submit
    res1 = client.get("/startGame")
    res1 = res1.data.decode("utf-8")
    response = json.loads(res1)
    token = response["player_id"]
    res = classify_helper(
        client, cfg.API_PATH_DATA, cfg.API_IMAGE5, time, token, user
    )
    assert(res.status == "200 OK")
    data = json.loads(res.data.decode("utf-8"))
    assert("certainty" in data)
    assert("guess" in data)
    assert("correctLabel" in data)
    assert("hasWon" in data)
    assert("gameState" in data)


def test_classify_white_image_done(client):
    """
        Ensure that the API returns the correct json data when an image
        consisting of only white pixels is submitted.
    """
    time = 0
    user = ""
    # Need to start a new game to get a token we can submit
    res1 = client.get("/startGame")
    res1 = res1.data.decode("utf-8")
    response = json.loads(res1)
    token = response["player_id"]
    res = classify_helper(
        client, cfg.API_PATH_DATA, cfg.API_IMAGE5, time, token, user
    )
    data = json.loads(res.data.decode("utf-8"))
    assert(data["gameState"] == "Done")


def test_classify_white_image_not_done(client):
    """
        Ensure that the API returns the correct json data when an image
        consisting of only white pixels is submitted.
    """
    time = 1
    user = ""
    # Need to start a new game to get a token we can submit
    res1 = client.get("/startGame")
    res1 = res1.data.decode("utf-8")
    response = json.loads(res1)
    token = response["player_id"]
    res = classify_helper(
        client, cfg.API_PATH_DATA, cfg.API_IMAGE5, time, token, user
    )
    data = json.loads(res.data.decode("utf-8"))
    assert(data["gameState"] == "Playing")


def test_classify_correct(client):
    """
        Ensure that the API returns no errors when the image submitted in the
        request complies with constraints and everything seem to be good.
    """
    # Username is not unique, can therefore use the same repeatedly
    name = "testing_api"
    time = 0
    # Need to start a new game to get a player_id we can submit
    res1 = client.get("/startGame")
    res1 = res1.data.decode("utf-8")
    response = json.loads(res1)
    player_id = response["player_id"]
    # submit answer with parameters and retrieve results
    res = classify_helper(
        client, cfg.API_PATH_DATA, cfg.API_IMAGE4, time, player_id, name
    )
    # Check if the correct response data is returned
    data = json.loads(res.data.decode("utf-8"))
    assert(isinstance(data, dict))
    # Check if the correct keys are included
    assert("certainty" in data)
    assert("hasWon" in data)
    # Check if 200 is returned
    assert(res.status_code == 200)


def test_allowedFile_small_resolution():
    """
        Test if the allowedFile function within the API returns False if an
        image with too small resolution is sent as parameter.
    """
    # Test the allowedFile function with the given filename.
    # The allowedFile function should return 'false'.
    with raises(excp.UnsupportedMediaType):
        allowed_file_helper(cfg.API_IMAGE1, False, "image/png")


def test_allowedFile_too_large_file():
    """
        Test if the allowedFile function within the API returns False if an
        image above the maximum size is sent as parameter.
    """
    # Test the allowedFile function with the given filename.
    # The allowedFile function should return 'false'.
    with raises(excp.UnsupportedMediaType):
        allowed_file_helper(cfg.API_IMAGE2, False, "image/png")


def test_allowedFile_wrong_format():
    """
        Test if the allowedFile function within the API returns False if an
        image of the wrong format is sent as parameter.
    """
    # Test the allowedFile function with the given filename.
    # The allowedFile function should return 'false'.
    with raises(excp.UnsupportedMediaType):
        allowed_file_helper(cfg.API_IMAGE3, False, "image/jpeg")


def test_allowedFile_correct():
    """
        Test if the allowedFile function within the API returns True if an
        image with all constraints satisfied is sent as parameter.
    """
    # Test the allowedFile function with the given filename.
    # The allowedFile function should return 'true'.
    allowed_file_helper(cfg.API_IMAGE4, True, "image/png")


def allowed_file_helper(filename, expected_result, content_type):
    """
        Helper function for the allowedFile function tests.
    """
    # Construct path to the directory with the images
    dir_path = construct_path(cfg.API_PATH_DATA)
    # The path is only valid if the program runs from the src directory
    path = os.path.join(dir_path, filename)
    with open(path, "rb") as f:
        data_stream = f.read()
        # Create temporary file and reset seek to avoid EOF errors
        tmp = tempfile.SpooledTemporaryFile()
        tmp.write(data_stream)
        tmp.seek(0)
        # Create file storage object containing the image
        image = werkzeug.datastructures.FileStorage(stream=tmp, filename=path,
                                                    content_type=content_type)
        # Test allowedFile function with the image file
        return api.allowed_file(image)


def classify_helper(client, data_path, image, time, player_id, user):
    """
        Helper function which sends post request to client on /classify.
        The function returns the response given from the client

        client: client object to communicate with
        data_path: path to directory containing data
        image: name of the image in the directory given by data_path
        time: time used during game
        player_id: player_id used to validate session
        user: username of the player
    """
    # Construct path to the directory storing the test data
    dir_path = construct_path(data_path)
    path = os.path.join(dir_path, image)
    # Open image and retrieve bytes stream
    with open(path, "rb") as f:
        img_string = io.BytesIO(f.read())

    answer = {
        "image": (img_string, image),
        "player_id": player_id,
        "time": time
    }
    res = client.post(
        "/classify", content_type="multipart/form-data", data=answer)
    return res


def construct_path(dir_list):
    """
        Take in a list of directories in sequential order with regards to path
        order and construct a relative path to the last directory in the list.
    """
    # Add first element to path
    path = dir_list[0]
    # Iterate over the list (exclude 1st element)
    for elem in dir_list[1:]:
        # Append the remaining paths sequentially
        path = os.path.join(path, elem)

    return path


def test_view_highscore(client):
    """
        Test if highscore data is strucutred correctly, example of format:
        {"daily":[{"name":"mari","score":83}],
        "total":[{"name":"ole","score":105},{"name":"mari","score":83}]}
    """
    # get response
    res = client.get("/viewHighScore")
    response = json.loads(res.data)
    #check that data structure is correct
    if response["total"]:
        assert(isinstance(response, dict))
        assert(isinstance(response["daily"], list))
        assert(isinstance(response["total"], list))
        assert(isinstance(response["daily"][0], dict))
        assert(isinstance(response["total"][0], dict))


def test_white_image_true():
    """
        Test if the white_image function returns True if the image is
        completely white.
    """
    dir_path = construct_path(cfg.API_PATH_DATA)
    path = os.path.join(dir_path, cfg.API_IMAGE5)
    img = PIL.Image.open(path)
    white = api.white_image(img)
    assert(white is True)


def test_white_image_false():
    """
        Test if the white_image function returns False if the image isn't
        compeltely white.
    """
    dir_path = construct_path(cfg.API_PATH_DATA)
    path = os.path.join(dir_path, cfg.API_IMAGE1)
    img = PIL.Image.open(path)
    white = api.white_image(img)
    assert(white is False)


def test_white_image_data_keys():
    """
        Test if the white_image_data_function returns a data of the correct
        format (check if all keys are in the json object returned).
    """
    data, code = api.white_image_data("", 1, "game_id", "player_id")
    json_data = json.loads(data)
    assert("certainty" in json_data)
    assert("guess" in json_data)
    assert("correctLabel" in json_data)
    assert("hasWon" in json_data)
    assert("gameState" in json_data)
    assert(code == 200)


def test_white_image_data_playing():
    """
        Test if the white_image_data function returns the correct data and
        that state is "playing" when time_left parameter is larger than zero.
    """
    label = ""
    data, code = api.white_image_data(label, 1, "game_id", "player_id")
    json_data = json.loads(data)
    assert(json_data["gameState"] == "Playing")
    assert(json_data["correctLabel"] == label)
    assert(json_data["hasWon"] is False)
    assert(json_data["certainty"] == 1.0)
    assert(json_data["guess"] == setup.WHITE_IMAGE_GUESS)


def test_white_image_data_done(client):
    """
        Test if the white_image_data function returns the correct data and
        that state is "done" when time_left parameter is zero.
    """
    res = client.get("/startGame")
    player_id = json.loads(res.data)["player_id"]
    print("PLAYER_ID: " + player_id)
    game_id = models.get_player(player_id).game_id
    label = ""
    data, code = api.white_image_data(label, 0, game_id, player_id)
    json_data = json.loads(data)
    assert(json_data["gameState"] == "Done")
    assert(json_data["correctLabel"] == label)
    assert(json_data["hasWon"] is False)
    assert(json_data["certainty"] == 1.0)
    assert(json_data["guess"] == setup.WHITE_IMAGE_GUESS)
