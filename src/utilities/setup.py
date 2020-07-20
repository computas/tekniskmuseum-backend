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
# The guess provided to the user when the image is blank
WHITE_IMAGE_GUESS = "blank image"

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
