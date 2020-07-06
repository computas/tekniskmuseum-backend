"""
    Testfunctions for testing functions to manipualte the database. The
    functions is used on an identical test database.
"""

from webapp import api
from webapp import models
import uuid
import time
import pytest
from flask import Flask

token = uuid.uuid4().hex
start_time = time.time()


def test_create_tables():
    result = models.create_tables(api.app)
    assert result == "Models created!"


def test_insert_into_games():
    with api.app.app_context():
        result = models.insert_into_games(token, start_time, "sun")
    assert result == "Inserted"


def test_query_games():
    with api.app.app_context():
        result = models.query_game(token)
    # If result not string
    assert type(result) == "list"


def test_query_euqals_insert():
    token2 = uuid.uuid4().hex
    start_time = time.time()
    with api.app.app_context():
        models.insert_into_games(token2, start_time, "bench")
        expected_result = (start_time, "bench")
        result = models.query_game(token2)
    assert result == expected_result
