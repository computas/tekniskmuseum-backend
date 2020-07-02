"""
    Testfunctions for testing functions to manipualte the database. The
    functions is used on a identical test database.
"""

from webapp import api
from webapp import models


def test_create_tables():
    result = models.create_tables(api.app)

    assert result == "Models created!"

def test_insert_into_test_games():
    pass
