import pytest
from src import models
import uuid
import datetime
from src.utilities.difficulties import DifficultyId
import os
from main import create_app
from src.extensions import db as _db


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
    # Name of the labels for the DB tests
    LABELS = ["bird", "tree", "house"]
    # How long the test games last
    STATE = "playing"


@pytest.fixture(scope="session")
def app():
    app, socketio = create_app()
    app.config["TESTING"] = True

    with app.app_context():
        yield app, socketio


@pytest.fixture(scope="session")
def app_instance(app):
    app, _ = app

    with app.app_context():
        yield app


@pytest.fixture(scope="session")
def client(app):
    app, _ = app
    with app.test_client() as client:
        yield client


@pytest.fixture(scope="session")
def db(app):
    app, _ = app
    with app.app_context():
        models.insert_into_games(
            TestValues.GAME_ID,
            TestValues.LABELS,
            TestValues.TODAY,
            DifficultyId.Easy,
        )
        models.insert_into_players(
            TestValues.PLAYER_ID, TestValues.GAME_ID, TestValues.STATE
        )
        models.insert_into_scores(
            TestValues.PLAYER_ID, 599, TestValues.TODAY, DifficultyId.Easy
        )
        yield _db

    with app.app_context():
        models.delete_all_tables()


@pytest.fixture
def test_clients(app):
    app, socketio = app
    with app.app_context():
        with app.test_client() as flask_client:
            test_client1 = socketio.test_client(
                app, flask_test_client=flask_client
            )
            test_client2 = socketio.test_client(
                app, flask_test_client=flask_client
            )
            """ response = flask_client.get("/")
            assert response.status_code == 200 """
            yield flask_client, test_client1, test_client2

            test_client1.disconnect()
            test_client2.disconnect()


@pytest.fixture
def four_test_clients(app):
    app, socketio = app
    with app.app_context():
        with app.test_client() as flask_client:
            test_client1 = socketio.test_client(
                app, flask_test_client=flask_client
            )
            test_client2 = socketio.test_client(
                app, flask_test_client=flask_client
            )
            test_client3 = socketio.test_client(
                app, flask_test_client=flask_client
            )
            test_client4 = socketio.test_client(
                app, flask_test_client=flask_client
            )

            yield flask_client, test_client1, test_client2, test_client3, test_client4

            test_client1.disconnect()
            test_client2.disconnect()
            test_client3.disconnect()
            test_client4.disconnect()


# Return path to data folder where images for testing are saved
def get_data_folder_path():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    src_directory = os.path.dirname(current_directory)
    root_directory = os.path.dirname(src_directory)
    data_directory = os.path.join(root_directory, "data")

    return data_directory
