import sys
import os
from utilities.keys import Keys

# number of players in overall high score top list
TOP_N = 10
# Total number of games
NUM_GAMES = 3
# certainties from costum vision lower than this -> haswon=False
CERTAINTY_THRESHOLD = 0.7
# certainty threhold for saving images to BLOB storage for training
SAVE_CERTAINTY = 0.3
# custom vision can't have more than 10 iterations at a time, if more classifier.py will delete the oldest iteration
CV_MAX_ITERATIONS = 10
# can't upload more than 64 images at a time, if more
CV_MAX_IMAGES = 64
# The guess provided to the user when the image is blank
WHITE_IMAGE_GUESS = "blank image"
# Authorization cookie expiration time in minutes
SESSION_EXPIRATION_TIME = 10
# Maximum file size and minimum resolution for CV classification
MAX_IMAGE_SIZE = 4000000
MIN_RESOLUTION = 256
# Container names
CONTAINER_NAME_ORIGINAL = "oldimgcontainer"
CONTAINER_NAME_NEW = "newimgcontainer"
# Number of attempt to create a new container, to make sure old container is deleted by Azure.
CREATE_CONTAINER_TRIES = 10
# Waiting interval in seconds for creating new container after deletion
CREATE_CONTAINER_WAITER = 30


# Object used to initialize Flask instance
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

    # database settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "mssql+pyodbc://%s" % con_str

    # secret key for cookie encryption
    SECRET_KEY = Keys.get("SECRET_KEY")

    # cookie settings
    if Keys.get("IS_PRODUCTION") == "true":
        SESSION_COOKIE_SECURE = True
    else:
        SESSION_COOKIE_SECURE = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'None'
