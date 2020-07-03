"""
    Testfunctions for testing functions to manipualte the database. The
    functions is used on a identical test database.
"""

from webapp import api
from webapp import models
import uuid
import time

token = uuid.uuid4().hex
start_time = time.time()
label = "label"


def test_create_tables():

    result = models.create_tables(api.app)

    assert result == "Models created!"

def test_insert_into_games():
    models.insert_into_games(token, start_time, label)
    record = models.query_games(token)
    assert record.label == label
