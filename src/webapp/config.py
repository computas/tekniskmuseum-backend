"""
    Configuration class for connecting to azure database.
"""

import sys
import os
from utilities.keys import Keys


class Config:
    """
        Config settings for flask and sqlalchemy should be set here.
    """

    if "pytest" in sys.modules:
        # Connection string for test database
        con_str = Keys.get("TEST_DB_CONNECTION_STRING")
        pass

    else:
        # Database configuration string
        con_str = Keys.get("DB_CONNECTION_STRING")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = con_str
