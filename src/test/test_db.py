"""
    Testfunctions for testing functions to manipualte the database. The
    functions is used on a identical test database.
"""

from webapp import api
from webapp import models
import uuid
import time
import pytest

token = uuid.uuid4().hex
start_time = time.time()
label = "label"

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
def test_insert_into_test_games():
    start_time = time.time()
    result = models.insert_into_games(token, start_time, "sun")
    assert result == "Inserted"

@pytest.fixture(scope="session")
def test_query_tables():
   result = models.query_game(token)
   #if result not string
   assert type(result) == "list"

@pytest.fixture(scope="session")
def test_query_euqals_insert():
    token2 = uuid.uuid4().hex
    start_time = time.time()
    models.insert_into_games(token2, start_time, "bench")
    result = [start_time, "bench"]
    expected_result = models.query_game(token2)
    assert result == expected_result

    

