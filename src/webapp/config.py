import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utilities.keys import Keys


class Config:
    """
        Config settings for flask and sqlalchemy should be set here.
    """

    # Database configuration string
    con_str = Keys.get("DB_CONNECTION_STRING")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = con_str
