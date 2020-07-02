"""
    Testfunctions for testing functions to manipualte the database. The
    functions is used on a identical test database.
"""

from webapp import api
from webapp import models


def test_create_tables():
    models.create_all


def create_tables(app):
    """
        Something.
    """
    with api.app.app_context():
        api.db.create_all()



def test_insert_into_test_games():
