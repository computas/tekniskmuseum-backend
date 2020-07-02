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
    with open("./test/test_data/testfile.png") as fh:
        best_guess, probabilitites = classifier.predict_image(fh)

        assert type(bestguess) is str
        assert type(probabilitites) is dict

