"""
    Testfunctions for testing functions to manipualte the database. The
    functions is used on an identical test database.
"""
import os
import uuid
import time
from webapp import api
from webapp import models
import datetime
from pytest import raises
from werkzeug import exceptions as excp
from test import config as cfg


class Test_values():
    TOKEN = uuid.uuid4().hex
    GAME_ID = uuid.uuid4().hex
    TODAY = datetime.datetime.today()


def test_create_tables():
    """
        Check that the tables exists.
    """
    result = models.create_tables(api.app)
    assert result


def test_insert_into_games():
    """
        Check that records exists in Games table after inserting.
    """
    with api.app.app_context():
        result = models.insert_into_games(
            Test_values.GAME_ID, cfg.LABELS, Test_values.TODAY
        )

    assert result


def test_insert_into_scores():
    """
        Check that records exists in Scores table after inserting.
    """
    with api.app.app_context():
        result = models.insert_into_scores(
            "Test User", 500, Test_values.TODAY
        )

    assert result


def test_insert_into_player_in_game():
    """
        Check that record exists in PlayerInGame table after inserting.
    """
    with api.app.app_context():
        result = models.insert_into_player_in_game(
            Test_values.TOKEN, Test_values.GAME_ID, cfg.PLAY_TIME
        )

    assert result


def test_illegal_parameter_games():
    """
        Check that exception is raised when illegal arguments is passed
        into games table.
    """
    with raises(excp.BadRequest):
        models.insert_into_games(
            10, ["label1", "label2", "label3"], "date_time"
        )


def test_illegal_parameter_scores():
    """
        Check that exception is raised when illegal arguments is passed
        into scores table.
    """
    with raises(excp.BadRequest):
        models.insert_into_scores(100, "score", "01.01.2020")


def test_illegal_parameter_labels():
    """
        Check that exception is raised when illegal arguments is passed
        into games table.
    """
    with raises(excp.BadRequest):
        models.insert_into_labels(1, None)


def test_illegal_parameter_player_in_game():
    """
        Check that exception is raised when illegal arguments is passed
        into player in game table.
    """
    with raises(excp.BadRequest):
        models.insert_into_player_in_game(100, 200, 11)


def test_query_euqals_insert_games():
    """
        Check that inserted record is the same as record catched by query.
    """
    with api.app.app_context():
        result = models.get_record_from_game(Test_values.GAME_ID)

    assert result.labels == cfg.LABELS
    # Datetime assertion can't be done due to millisec differents


def test_query_equals_insert_player_in_game():
    """
        Check that inserted record is the same as record catched by query.
    """
    with api.app.app_context():
        result = models.get_record_from_player_in_game(Test_values.TOKEN)

    assert result.game_id == Test_values.GAME_ID
    assert result.play_time == cfg.PLAY_TIME


def test_get_daily_high_score_sorted():
    """
        Check that daily high score list is sorted.
    """
    # insert random data into db
    with api.app.app_context():
        for i in range(5):
            result = models.insert_into_scores(
                "Test User",
                10 + i,
                datetime.date.today() - datetime.timedelta(days=i),
            )
            assert result

    with api.app.app_context():
        result = models.get_daily_high_score()
    sorting_check_helper(result)


def test_get_top_n_high_score_list_sorted():
    """
        Check that total high score list is sorted.
    """
    with api.app.app_context():
        result = models.get_top_n_high_score_list(10)

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


def test_get_iteration_name():
    with api.app.app_context():
        iteration_name = models.get_iteration_name()

    assert isinstance(iteration_name, str)


def test_get_n_labels_correct_size():
    """
        Test that get_n_labels return lists of correct sizes
    """
    with api.app.app_context():
        for i in range(5):
            result = models.get_n_labels(i)
            assert len(result) == i


def test_get_n_labels_bad_reqeust():
    """
        Test that get_n_labels raises exeption if n is larger than number of labels
    """
    with raises(Exception):
        models.get_n_labels(10000)


def test_to_norwegian_correct_translation():
    """
        Test that to_norwegian translates words correctly
    """
    english_words = ["mermaid", "axe", "airplane"]
    norwgian_words = ["havfrue", "øks", "fly"]

    with api.app.app_context():
        for i in range(0, len(english_words)):
            translation = models.to_norwegian(english_words[i])
            print(translation)
            assert (translation == norwgian_words[i])


def test_to_norwegian_illegal_parameter():
    """
        Test that to_norwegian raises exeption if input word is not found
    """
    with raises(Exception):
        models.get_n_labels("this word is not in the database")
