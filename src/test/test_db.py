"""
    Testfunctions for testing functions to manipualte the database. The
    functions is used on an identical test database.
"""

from webapp import api
from webapp import models
import uuid
import time
import unittest
import datetime

token = uuid.uuid4().hex
start_time = time.time()


def test_create_tables():
    """
        Check that the tables exists.
    """
    result = models.create_tables(api.app)
    assert result == "Models created!"


def test_insert_into_games():
    """
        Check that records exists in Games table.
    """
    with api.app.app_context():
        result = models.insert_into_games(token, start_time, "sun")

    assert result == "Inserted"


def test_insert_into_scores():
    """
        Check that records exists in Scores table.
    """
    date = datetime.date.today()
    with api.app.app_context():
        result = models.insert_into_scores("Test User", 500, date)

    assert result == "Inserted"


class test(unittest.TestCase):
    """
        Class for using unittest.TestCase for asserting exceptions.
    """

    def test_illegal_parameter_games(self):
        """
            Check that exception is raised when illegal arguments is passed
            into games table.
        """
        with api.app.app_context():
            self.assertRaises(AttributeError, models.insert_into_games,
                              "token", "time", 10)

    def test_illegal_parameter_scores(self):
        """
            Check that exception is raised when illegal arguments is passed
            into scores table.
        """
        with api.app.app_context():
            self.assertRaises(AttributeError, models.insert_into_scores,
                              100, "score", "01.01.2020")


def test_query_euqals_insert():
    """
        Check that inserted record is the same as record catched by query.
    """
    token2 = uuid.uuid4().hex
    start_time = time.time()
    with api.app.app_context():
        models.insert_into_games(token2, start_time, "bench")
        expected_result = (start_time, "bench")
        result = models.query_game(token2)

    assert result == expected_result


def test_get_daily_high_score_sorted():
    """
        Check that daily high score list is sorted.
    """
    with api.app.app_context():
        result = models.get_daily_high_score()

    sorting_check_helper(result)


def test_get_top_n_high_score_list_sorted():
    """
        Check that total high score list is sorted.
    """
    with api.app.app_context():
        result = models.get_daily_high_score()

    sorting_check_helper(result)


def sorting_check_helper(high_score_list):
    """
        Helper function for testing if a list of score is sorted by scores, descending.
    """
    prev_score = high_score_list[0]["score"]
    for player in high_score_list[1:]:
        assert player["score"] <= prev_score
        prev_score = player["score"]


def test_get_daily_high_score_structure():
    """
        Check that highscore data has correct attributes: score and name
    """
    with api.app.app_context():
        result = models.get_daily_high_score()

    for player in result:
        assert "score" in player
        assert "name" in player


def test_get_top_n_high_score_list_structure():
    """
        Check that highscore data has correct attributes: score and name
    """
    with api.app.app_context():
        result = models.get_top_n_high_score_list(10)

    for player in result:
        assert "score" in player
        assert "name" in player


'''
def test_clear_table():
    """
        Check that number of rows is zero after clearing both tables.
    """
    with api.app.app_context():
        models.clear_table("Games")
        models.clear_table("Scores")
        games_rows = models.get_size_of_table("Games")
        scores_rows = models.get_size_of_table("Scores")

    assert games_rows == 0
    assert scores_rows == 0
'''
