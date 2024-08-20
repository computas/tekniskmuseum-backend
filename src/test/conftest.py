import pytest
from webapp.api import app, models
import uuid
import datetime
from src.utilities.difficulties import DifficultyId


class TestValues:
    PLAYER_ID = uuid.uuid4().hex
    GAME_ID = uuid.uuid4().hex
    TODAY = datetime.datetime.today()
    CV_ITERATION_NAME = "Iteration5"
    DIFFICULTY_ID = DifficultyId.Easy
    # Path to the image used to test allowedFile. Image must be smaller than 256 px
    API_IMAGE1 = "allowedFile_test1.png"
    # Path to the image used to test allowedFile. Image must be larger than 4000000 bits
    API_IMAGE2 = "allowedFile_test2.png"
    # Path to the image used to test allowedFile. Image must no have .png format
    API_IMAGE3 = "allowedFile_test3.jpg"
    # Path to the image used to test allowedFile with correct input
    API_IMAGE4 = "allowedFile_test4.png"
    # Path to the image used to test the white_image function
    API_IMAGE5 = "white_image.png"
    # Path to the image used to test allowedFile. Image must include colors (not only white pixels)
    API_IMAGE6 = "allowedFile_test6.png"
    # test file for customvision module
    CV_TEST_IMAGE = "cv_testfile.png"
    # Contains in-order sequence to the directory with images used to test
    # the allowedFile function
    API_PATH_DATA = ["..", "data"]
    # Name of the labels for the DB tests
    LABELS = ["bird", "tree", "house"]
    # How long the test games last
    STATE = "playing"


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
            TestValues.GAME_ID, TestValues.LABELS, TestValues.TODAY, DifficultyId.Easy
        )
        models.insert_into_players(
            TestValues.PLAYER_ID, TestValues.GAME_ID, TestValues.STATE
        )
        models.insert_into_scores(
            TestValues.PLAYER_ID, 599, TestValues.TODAY, DifficultyId.Easy)

    yield

    models.delete_all_tables()
