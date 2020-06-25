import sys
import werkzeug
import pytest

sys.path.insert(1, "./flask")
import api


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
    pass


def test_allowedFile_too_large_file(client):
    """
        Test if the allowedFile function within the API returns False if an
        image above the maximum size is sent as parameter.
    """
    pass


def test_allowedFile_wrong_format(client):
    """
        Test if the allowedFile function within the API returns False if an
        image of the wrong format is sent as parameter.
    """
    pass


def test_allowedFile_correct(client):
    """
        Test if the allowedFile function within the API returns True if an
        image with all constraints satisfied is sent as parameter.
    """
    pass
