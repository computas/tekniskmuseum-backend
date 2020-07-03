"""
    Testfunctions for testing functions to manipualte the database. The
    functions is used on a identical test database.
"""

from webapp import api
from webapp import models

token = uuid.uuid4().hex

def test_create_tables():
    result = models.create_tables(api.app)

    assert result == "Models created!"

def test_insert_into_test_games():
    start_time = time.time()
    result = models.insert_into_games(token, start_time, "sun")
    assert result == "Inserted"

def test_query_tables():
   result = models.query_game(token)
   #if result not string
   assert type(result) == "list"


def test_query_euqals_insert():
    token2 = uuid.uuid4().hex
    start_time = time.time()
    models.insert_into_scores(token2, start_time, "bench")
    result = [start_time, "bench"]
    expected_result = models.query_game(token2)
    assert result == expected_result





