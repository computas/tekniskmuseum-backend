"""
    Testfunctions for testing functions to manipualte the database. The
    functions is used on an identical test database.
"""

import datetime
from src.utilities.difficulties import DifficultyId
from src import models
from pytest import raises
from werkzeug import exceptions as excp
import json
from test.conftest import TestValues


def test_create_tables(app_instance):
    """
    Check that the tables exists.
    """
    result = models.create_tables(app_instance)
    assert result


def test_insert_into_games(app_instance):
    """
    Check that records exists in Games table after inserting.
    """
    with app_instance.app_context():
        result = models.insert_into_games(
            str(TestValues.GAME_ID),
            json.dumps(TestValues.LABELS),
            TestValues.TODAY,
            TestValues.DIFFICULTY_ID,
        )

    assert result


def test_insert_into_players(app_instance):
    """
    Check that record exists in PlayerInGame table after inserting.
    """
    with app_instance.app_context():
        result = models.insert_into_players(
            TestValues.PLAYER_ID, TestValues.GAME_ID, TestValues.STATE
        )

    assert result


def test_insert_into_scores(app_instance):
    """
    Check that records exists in Scores table after inserting.
    """
    with app_instance.app_context():
        result = models.insert_into_scores(
            TestValues.PLAYER_ID,
            500,
            TestValues.TODAY,
            TestValues.DIFFICULTY_ID,
        )

    assert result


def test_illegal_parameter_games():
    """
    Check that exception is raised when illegal arguments is passed
    into games table.
    """
    with raises(excp.BadRequest):
        models.insert_into_games(
            10, ["label1", "label2", "label3"], "date_time", "diff_id"
        )


def test_illegal_parameter_scores():
    """
    Check that exception is raised when illegal arguments is passed
    into scores table.
    """
    with raises(excp.BadRequest):
        models.insert_into_scores(
            100, "score", "01.01.2020", DifficultyId.Medium
        )


def test_illegal_parameter_labels():
    """
    Check that exception is raised when illegal arguments is passed
    into games table.
    """
    with raises(excp.BadRequest):
        models.insert_into_labels(1, None, TestValues.DIFFICULTY_ID)


def test_illegal_parameter_players():
    """
    Check that exception is raised when illegal arguments is passed
    into player in game table.
    """
    with raises(excp.BadRequest):
        models.insert_into_players(100, 200, 11)


def test_query_equals_insert_games(app_instance):
    """
    Check that inserted record is the same as record catched by query.
    """
    with app_instance.app_context():
        result = models.get_game(TestValues.GAME_ID)

    assert result.labels == json.dumps(
        TestValues.LABELS
    )  # Datetime assertion can't be done due to millisec differents


def test_query_equals_insert_players(app_instance):
    """
    Check that inserted record is the same as record catched by query.
    """
    with app_instance.app_context():
        result = models.get_player(TestValues.PLAYER_ID)

    assert result.game_id == TestValues.GAME_ID
    assert result.state == TestValues.STATE


def test_get_daily_high_score_sorted(app_instance):
    """
    Check that daily high score list is sorted.
    """
    # insert random data into db
    with app_instance.app_context():
        for i in range(5):
            result = models.insert_into_scores(
                TestValues.PLAYER_ID,
                10 + i,
                datetime.date.today() - datetime.timedelta(days=i),
                TestValues.DIFFICULTY_ID,
            )
            assert result

    with app_instance.app_context():
        result = models.get_daily_high_score(TestValues.DIFFICULTY_ID)
    sorting_check_helper(result)


def test_get_top_n_high_score_list_sorted(app_instance):
    """
    Check that total high score list is sorted.
    """
    with app_instance.app_context():
        result = models.get_top_n_high_score_list(10, TestValues.DIFFICULTY_ID)

    sorting_check_helper(result)


def sorting_check_helper(high_score_list):
    """
    Helper function for testing if a list of score is sorted by scores, descending.
    """
    prev_score = high_score_list[0]["score"]
    for player in high_score_list[1:]:
        assert player["score"] <= prev_score
        prev_score = player["score"]


def test_get_daily_high_score_structure(app_instance):
    """
    Check that highscore data has correct attributes: score and name
    """
    with app_instance.app_context():
        result = models.get_daily_high_score(TestValues.DIFFICULTY_ID)

    for player in result:
        assert "score" in player
        assert "id" in player


def test_get_top_n_high_score_list_structure(app_instance):
    """
    Check that highscore data has correct attributes: score and name
    """
    with app_instance.app_context():
        result = models.get_top_n_high_score_list(10, TestValues.DIFFICULTY_ID)

    for player in result:
        assert "score" in player
        assert "id" in player


def test_get_n_labels_correct_size(app_instance):
    """
    Test that get_n_labels return lists of correct sizes
    """
    with app_instance.app_context():
        for i in range(1, 5):
            result = models.get_n_labels(i, TestValues.DIFFICULTY_ID)
            assert len(result) == i


def test_get_n_labels_bad_request():
    """
    Test that get_n_labels raises exeption if n is larger than number of labels
    """
    with raises(Exception):
        models.get_n_labels(10000)


def test_to_norwegian_correct_translation(app_instance):
    """
    Test that to_norwegian translates words correctly
    """
    english_words = ["mermaid", "axe", "airplane"]
    norwgian_words = ["havfrue", "øks", "fly"]

    with app_instance.app_context():
        for i in range(0, len(english_words)):
            translation = models.to_norwegian(english_words[i])
            assert translation == norwgian_words[i]


def test_to_norwegian_illegal_parameter():
    """
    Test that to_norwegian raises exeption if input word is not found
    """
    with raises(Exception):
        models.to_norwegian("this word is not in the database")


def test_high_score_cleared(app_instance):
    """
    Check if high score table empty.
    """
    with app_instance.app_context():
        models.clear_highscores()
        num_records = models.Scores.query.count()

    assert num_records == 0
