import os
import sys
import werkzeug
import tempfile
import pytest
from application import api


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
    req = client.get('/')
    assert(req.data == b'Hello, World!')


def test_allowedFile_small_resolution(client):
    """
        Test if the allowedFile function within the API returns False if an
        image with too small resolution is sent as parameter.
    """
    # Test the allowedFile function with the given filename.
    # The allowedFile function should return 'false'.
    allowedFileHelper("allowedFile_test1.png", False)


def test_allowedFile_too_large_file(client):
    """
        Test if the allowedFile function within the API returns False if an
        image above the maximum size is sent as parameter.
    """
    # Test the allowedFile function with the given filename.
    # The allowedFile function should return 'false'.
    allowedFileHelper("allowedFile_test2.png", False)


def test_allowedFile_wrong_format(client):
    """
        Test if the allowedFile function within the API returns False if an
        image of the wrong format is sent as parameter.
    """
    # Test the allowedFile function with the given filename.
    # The allowedFile function should return 'false'.
    allowedFileHelper("allowedFile_test3.jpg", False)


def test_allowedFile_correct(client):
    """
        Test if the allowedFile function within the API returns True if an
        image with all constraints satisfied is sent as parameter.
    """
    # Test the allowedFile function with the given filename.
    # The allowedFile function should return 'true'.
    allowedFileHelper("allowedFile_test4.png", True)


def allowedFileHelper(filename, expected_result):
    """
        Helper function for the allowedFile function tests.
    """
    # The path is only valid if the program runs from the outmost directory
    path = os.path.join('test', 'test_data', filename)
    with open(path, 'rb') as f:
        data_stream = f.read()
        # Create temporary file and reset seek to avoid EOF errors
        tmp = tempfile.SpooledTemporaryFile()
        tmp.write(data_stream)
        tmp.seek(0)
        # Create file storage object containing the image
        image = werkzeug.datastructures.FileStorage(
            stream=tmp,
            filename=path
        )
        # Test allowedFile function with the image file
        result = api.allowedFile(image)

    assert(result == expected_result)
