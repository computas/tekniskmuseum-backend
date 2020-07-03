"""
    Testfunctions for testing functions to manipualte the database. The
    functions is used on a identical test database.
"""

from webapp import api
from webapp import models

token = uuid.uuid4().hex
start_time = time.time()
label = "test label"


def test_create_tables():

    result = models.create_tables(api.app)

    assert result == "Models created!"

def test_insert_into_test_games():
    models.insert_into_games(token, start_time, label)
    record = models.query_games(token)
    assert 
