import os
import sys
import werkzeug
import tempfile
import pytest
from webapp import api
from test import config as cfg


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
    req = client.get("/")
    assert req.data == b"Yes, we're up"


def test_start_game_wrong_request(client):
    """
        Ensure that the API returns error due to unsupported request type
        (something else than GET).
    """
    # send request to test client with empty dictionary
    req = client.post("/startGame", data=dict())
    assert(b"405 Method Not Allowed" in req.data)


def test_start_game_correct(client):
    """
        Ensure that the API doesn't return error when sumitting a GET request.
    """
    req = client.get("/startGame", data=dict())
    # Ensure that the returned dictionary contains a label, start time
    # and a token.
    assert(b"label" in req.data)
    assert(b"start_time" in req.data)
    assert(b"token" in req.data)


def test_submit_answer_wrong_request(client):
    """
        Ensure that the API returns error due to unsupported request type
        (something else than POST).
    """
    # Submit GET request, since POST is required
    req = client.get("/submitAnswer")
    assert(b"405 Method Not Allowed" in req.data)


def test_submit_answer_no_image(client):
    """
        Ensure that the API returns error when there is no image submitted
        in the request.
    """
    # Since the API checks if the image is there before anything else,
    # we don't need to include anything with the request
    req = client.post("submitAnswer", data=dict())
    # Check if the correct message is returned
    assert(b"No image submitted" == req.data)
    # Check if the correct error code is returned
    assert(req.status_code == 400)


def test_submit_answer_wrong_image(client):
    """

    """
    pass


def test_submit_answer_correct(client):
    """

    """
    pass



def test_allowedFile_small_resolution():
    """
        Test if the allowedFile function within the API returns False if an
        image with too small resolution is sent as parameter.
    """
    # Test the allowedFile function with the given filename.
    # The allowedFile function should return 'false'.
    allowed_file_helper(cfg.api_image1, False)


def test_allowedFile_too_large_file():
    """
        Test if the allowedFile function within the API returns False if an
        image above the maximum size is sent as parameter.
    """
    # Test the allowedFile function with the given filename.
    # The allowedFile function should return 'false'.
    allowed_file_helper(cfg.api_image2, False)


def test_allowedFile_wrong_format():
    """
        Test if the allowedFile function within the API returns False if an
        image of the wrong format is sent as parameter.
    """
    # Test the allowedFile function with the given filename.
    # The allowedFile function should return 'false'.
    allowed_file_helper(cfg.api_image3, False)


def test_allowedFile_correct():
    """
        Test if the allowedFile function within the API returns True if an
        image with all constraints satisfied is sent as parameter.
    """
    # Test the allowedFile function with the given filename.
    # The allowedFile function should return 'true'.
    allowed_file_helper(cfg.api_image4, True)


def allowed_file_helper(filename, expected_result):
    """
        Helper function for the allowedFile function tests.
    """
    # Construct path to the directory with the images
    dir_path = construct_path(cfg.api_path_data)
    # The path is only valid if the program runs from the src directory
    path = os.path.join(dir_path, filename)
    with open(path, "rb") as f:
        data_stream = f.read()
        # Create temporary file and reset seek to avoid EOF errors
        tmp = tempfile.SpooledTemporaryFile()
        tmp.write(data_stream)
        tmp.seek(0)
        # Create file storage object containing the image
        image = werkzeug.datastructures.FileStorage(stream=tmp, filename=path)
        # Test allowedFile function with the image file
        result = api.allowed_file(image)

    assert result == expected_result


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
