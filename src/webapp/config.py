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

<<<<<<< HEAD
    if "pytest" in sys.modules:
        # Insert connection string for test database
        pass

    else:
        # Database configuration string
        con_str = Keys.get("DB_CONNECTION_STRING")
=======
    # Database configuration string
    con_str = Keys.get("DB_CONNECTION_STRING")
>>>>>>> a6ed3d1202ca59b0b4e27f97b74b4dd7b11aa5e0

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = con_str
