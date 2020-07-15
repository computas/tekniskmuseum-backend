import sys
import os
from utilities.keys import Keys


# number of players in overall high score top list
TOP_N = 10
# Total number of games
NUM_GAMES = 3
# certainties from costum vision lower than this -> haswon=False
CERTAINTY_THRESHOLD = 0.5
# custom vision can't have more than 10 iterations at a time, if more classifier.py will delete the oldest iteration
CV_MAX_ITERATIONS = 10
# can't upload more than 64 images at a time, if more
CV_MAX_IMAGES = 64
# USED BY API
LABELS = [
    "airplane",
    "angel",
    "ant",
    "apple",
    "axe",
    "bathtub",
    "beach",
    "bee",
    "bicycle",
    "birthday cake",
    "book",
    "bus",
    "butterfly",
    "calculator",
    "camel",
    "castle",
    "cat",
    "cow",
    "crab",
    "crocodile",
    "diamond",
    "elephant",
    "eye",
    "frying pan",
    "giraffe",
    "hammer",
    "hand",
    "helicopter",
    "horse",
    "hospital",
    "key",
    "lightning",
    "mermaid",
    "mountain",
    "ocean",
    "palm tree",
    "piano",
    "pineapple",
    "pizza",
    "police car",
    "screwdriver",
    "sheep",
    "snail",
    "suitcase",
    "tractor",
    "watermelon",
    "wheel",
    "wristwatch",
]


class Flask_config:
    """
        Config settings for flask and sqlalchemy should be set here.
    """

    if "pytest" in sys.modules or "DEBUG" in os.environ:
        # Connection string for test database
        con_str = Keys.get("TEST_DB_CONNECTION_STRING")

    else:
        # Connection string for production database
        con_str = Keys.get("DB_CONNECTION_STRING")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = con_str
