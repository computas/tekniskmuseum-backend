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
top_n = 10  # number of players in overall high score top list


# Config Flask
class Flask_config:
    """
        Config settings for flask and sqlalchemy should be set here.
    """

    if "pytest" in sys.modules:
        # Connection string for test database
        con_str = Keys.get("TEST_DB_CONNECTION_STRING")

    else:
        # Database configuration string
        con_str = Keys.get("DB_CONNECTION_STRING")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = con_str
