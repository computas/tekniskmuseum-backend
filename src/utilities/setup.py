import sys
from utilities.keys import Keys

# USED BY CUSTOM VISION
# custom vision can't have more than 10 iterations at a time, if more classifier.py will delete the oldest iteration
CV_MAX_ITERATIONS = 10
# can't upload more than 64 images at a time, if more
CV_MAX_IMAGES = 64


# USED BY API
labels = [
    "ambulance",
    "bench",
    "circle",
    "square",
    "star",
    "sun",
    "triangle",
]
time_limit = 22  # time limit for one guess
num_games = 3
certainty_threshold = 0.05 # certainties from costum vision lower than this -> haswon=False


# Config Flask
class Flask_config:
    """
        Config settings for flask and sqlalchemy should be set here.
    """

    if "pytest" in sys.modules:
        # Connection string for test database
        con_str = Keys.get("TEST_DB_CONNECTION_STRING")

    else:
        # Connection string for production database
        con_str = Keys.get("DB_CONNECTION_STRING")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = con_str
