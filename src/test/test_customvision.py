import pytest
import os
from customvision.classifier import Classifier
from test.conftest import TestValues, get_data_folder_path


@pytest.fixture
def classifier():
    """
    initialize custom vision classifer object.
    """
    yield Classifier()


def test_prediction_image_does_not_crash(classifier):
    """
    assert classifier is able to get a predicition without crashing.
    """
    path = os.path.join(get_data_folder_path(), TestValues.CV_TEST_IMAGE)
    with open(path, "rb") as fh:
        try:
            best_guess, probabilitites = classifier.predict_image(fh)
        except Exception:
            assert False
        assert True


def test_best_guess_is_string(classifier):
    """
    Test that the best guess from the classifier is a string.
    """
    path = os.path.join(get_data_folder_path(), TestValues.CV_TEST_IMAGE)
    with open(path, "rb") as fh:
        probabilities, best_guess = classifier.predict_image(fh)
        assert type(best_guess) is str


def test_probabilities_format(classifier):
    """
    Test that the probability items are of the correct type.
    """
    path = os.path.join(get_data_folder_path(), TestValues.CV_TEST_IMAGE)
    with open(path, "rb") as fh:
        probabilities, best_guess = classifier.predict_image(fh)
        assert type(probabilities) is dict
        for k, v in probabilities.items():
            assert type(k) is str
            assert type(v) is float


def test_get_iteration_name_length(classifier):
    """
    Test if the result returned has specified length
    """
    assert classifier.iteration_name == TestValues.CV_ITERATION_NAME


def test_get_iteration_name_is_string(classifier):
    """
    Tests if it's possible to get an iteration name from the database and the type is str
    """
    assert isinstance(classifier.iteration_name, str)
