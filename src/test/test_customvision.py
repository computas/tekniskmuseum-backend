import pytest
import os
from customvision.classifier import Classifier
from test.test_api import construct_path
from test.conftest import TestValues


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
    path = construct_path(TestValues.API_PATH_DATA)
    path = os.path.join(path, TestValues.CV_TEST_IMAGE)
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
    path = construct_path(TestValues.API_PATH_DATA)
    path = os.path.join(path, TestValues.CV_TEST_IMAGE)
    with open(path, "rb") as fh:
        probabilities, best_guess = classifier.predict_image(fh)
        assert type(best_guess) is str


def test_probabilities_format(classifier):
    """
        Test that the probability items are of the correct type.
    """
    path = construct_path(TestValues.API_PATH_DATA)
    path = os.path.join(path, TestValues.CV_TEST_IMAGE)
    with open(path, "rb") as fh:
        probabilities, best_guess = classifier.predict_image(fh)
        assert type(probabilities) is dict
        for k, v in probabilities.items():
            assert type(k) is str
            assert type(v) is float
