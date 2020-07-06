"""
    Testfunctions for testing functions to manipualte the database. The
    functions is used on an identical test database.
"""

from webapp import api
from webapp import models
import uuid
import time
import pytest
import pdb

token = uuid.uuid4().hex
start_time = time.time()


@pytest.fixture(scope="session")
def client():
    """
        Pytest fixture which configures application for testing.
    """
    api.app.config["TESTING"] = True
    with api.app.test_client() as client:
        yield client


def test_create_tables():
    result = models.create_tables(api.app)
    assert result == "Models created!"


@pytest.fixture(scope="session")
def test_insert_into_games():
    result = models.insert_into_games(token, start_time, "sun")
    breakpoint()
    assert result == "Inserted"


@pytest.fixture(scope="session")
def test_query_games():
    result = models.query_game(token)
    # If result not string
    assert type(result) == "list"


@pytest.fixture(scope="session")
def test_query_euqals_insert():
    token2 = uuid.uuid4().hex
    start_time = time.time()
    models.insert_into_games(token2, start_time, "bench")
    expected_result = [start_time, "bench"]
    result = models.query_game(token2)
    assert result == expected_result
