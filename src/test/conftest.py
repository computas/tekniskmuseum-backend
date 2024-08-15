import pytest
from webapp.api import app, models
import uuid
import datetime
from src.utilities.difficulties import DifficultyId
from test import config as cfg


class TestValues:
    PLAYER_ID = uuid.uuid4().hex
    GAME_ID = uuid.uuid4().hex
    TODAY = datetime.datetime.today()
    CV_ITERATION_NAME_LENGTH = 36


@pytest.fixture(scope="session")
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            pass
        yield client


@pytest.fixture(scope="session")
def db():
    with app.app_context():
        models.insert_into_games(
            TestValues.GAME_ID, cfg.LABELS, TestValues.TODAY, DifficultyId.Easy
        )
        models.insert_into_players(
            TestValues.PLAYER_ID, TestValues.GAME_ID, cfg.STATE
        )
        models.insert_into_scores(
            TestValues.PLAYER_ID, 599, TestValues.TODAY, DifficultyId.Easy)

    yield

    models.delete_all_tables()
