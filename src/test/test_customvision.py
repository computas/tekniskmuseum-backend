import pytest
from customvision.classifier import Classifier


@pytest.fixture
def classifier():
    """
        initialize custom vision classifer object
    """
    with Classifier() as clf:
        yield clf


def test_prediction_image_does_not_crash(classifier):
    """
        assert classifier is able to get a predicition without crashing
    """

    best_guess, probabilitites = classifier.predict_image()
    # assert()

