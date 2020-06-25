import sys
import pytest
import api

sys.path.insert(1, "./flask")


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
    assert req.data == b"Hello, World!"
